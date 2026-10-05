import { createClient } from "npm:@supabase/supabase-js@2";

// Stripe -> PetsAIHealth Plus. Authenticated by the Stripe signature (STRIPE_WEBHOOK_SECRET), not a JWT (verify_jwt=false).
// Events: checkout.session.completed (link app email <-> Stripe customer), invoice.paid (extend access),
// customer.subscription.deleted / .updated(canceled) and charge.refunded (end access).
const enc = new TextEncoder();
const GRACE_SECONDS = 3 * 86400;

function hex(buf: ArrayBuffer) {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function verify(payload: string, header: string, secret: string, tolerance = 300) {
  let t: string | null = null;
  const v1: string[] = [];
  for (const part of header.split(",")) {
    const [k, v] = part.trim().split("=");
    if (k === "t") t = v;
    else if (k === "v1") v1.push(v);
  }
  if (!t || !v1.length) return false;
  if (Math.abs(Date.now() / 1000 - Number(t)) > tolerance) return false;
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const expected = hex(await crypto.subtle.sign("HMAC", key, enc.encode(`${t}.${payload}`)));
  return v1.some((s) => {
    if (s.length !== expected.length) return false;
    let d = 0;
    for (let i = 0; i < s.length; i++) d |= s.charCodeAt(i) ^ expected.charCodeAt(i);
    return d === 0;
  });
}

const json = (o: unknown, status = 200) =>
  new Response(JSON.stringify(o), { status, headers: { "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ ok: true });
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  // Signing secret: edge-function env STRIPE_WEBHOOK_SECRET, else Supabase Vault (public.get_stripe_webhook_secret, service_role only).
  let secret = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";
  if (!secret) {
    const { data } = await sb.rpc("get_stripe_webhook_secret");
    secret = (data as string) ?? "";
  }
  if (!secret) return json({ error: "webhook secret not configured" }, 500);
  const body = await req.text();
  const sig = req.headers.get("stripe-signature") ?? "";
  if (!(await verify(body, sig, secret))) return json({ error: "bad signature" }, 400);

  const event = JSON.parse(body);
  const obj = event.data?.object ?? {};

  try {
    if (event.type === "checkout.session.completed") {
      const email = String(obj.client_reference_id || obj.customer_details?.email || "").toLowerCase();
      if (email && obj.customer) {
        const { data: existing } = await sb.from("subscriptions").select("user_email").eq("user_email", email).limit(1);
        const ids = { stripe_customer_id: obj.customer, stripe_subscription_id: obj.subscription ?? null };
        if (existing && existing.length) {
          await sb.from("subscriptions").update(ids).eq("user_email", existing[0].user_email);
        } else {
          await sb.from("subscriptions").insert({ user_email: email, plan: "free", ...ids, notes: "stripe checkout" });
        }
        // invoice.paid may have arrived first under the billing email: carry its access over.
        const { data: other } = await sb.from("subscriptions").select("user_email,plan,valid_until")
          .eq("stripe_customer_id", obj.customer).neq("user_email", existing?.[0]?.user_email ?? email).eq("plan", "plus").limit(1);
        if (other && other.length) {
          await sb.from("subscriptions").update({ plan: "plus", valid_until: other[0].valid_until })
            .eq("user_email", existing?.[0]?.user_email ?? email);
        }
      }
    } else if (event.type === "invoice.paid") {
      const ends = (obj.lines?.data ?? []).map((l: any) => l.period?.end).filter(Boolean);
      const end = ends.length ? Math.max(...ends) : Math.floor(Date.now() / 1000) + 31 * 86400;
      const validUntil = new Date((end + GRACE_SECONDS) * 1000).toISOString();
      let target: string | null = null;
      if (obj.customer) {
        const { data } = await sb.from("subscriptions").select("user_email").eq("stripe_customer_id", obj.customer).limit(1);
        if (data && data.length) target = data[0].user_email;
      }
      if (!target && obj.customer_email) target = String(obj.customer_email).toLowerCase();
      if (target) {
        await sb.from("subscriptions").upsert({
          user_email: target, plan: "plus", valid_until: validUntil,
          stripe_customer_id: obj.customer ?? null, stripe_subscription_id: obj.subscription ?? null,
          notes: `stripe invoice ${obj.id}`,
        }, { onConflict: "user_email" });
      }
    } else if (event.type === "charge.refunded") {
      // Fully refunded payment -> end access now (partial refunds keep access).
      if (obj.refunded === true && obj.customer) {
        await sb.from("subscriptions").update({ valid_until: new Date().toISOString(), notes: `stripe refund ${obj.id}` })
          .eq("stripe_customer_id", obj.customer);
      }
    } else if (event.type === "customer.subscription.updated") {
      if (["canceled", "unpaid", "incomplete_expired"].includes(obj.status)) {
        await sb.from("subscriptions").update({ valid_until: new Date().toISOString(), notes: `stripe subscription ${obj.status}` })
          .eq("stripe_subscription_id", obj.id);
      }
    } else if (event.type === "customer.subscription.deleted") {
      await sb.from("subscriptions").update({ valid_until: new Date().toISOString(), notes: "stripe subscription ended" })
        .eq("stripe_subscription_id", obj.id);
    }
  } catch (e) {
    return json({ error: String(e) }, 500); // Stripe will retry
  }
  return json({ received: true });
});
