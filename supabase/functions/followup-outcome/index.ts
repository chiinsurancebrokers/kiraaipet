import { createClient } from "npm:@supabase/supabase-js@2";

// One-tap outcome from the follow-up e-mail: GET ?id=<followups.id>&o=ok|worse&t=<hmac>&l=el|en shows a confirm button; the POST records it.
// Authenticated by the HMAC (FOLLOWUP_SIGNING_SECRET), not a JWT: deploy with verify_jwt=false. Records the outcome once on the
// followups row and a code-only row in safety_events (no e-mail, no pet name).
const enc = new TextEncoder();
const hex = (b: ArrayBuffer) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");

async function token(id: string, outcome: string, secret: string) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", key, enc.encode(`${id}:${outcome}`))).slice(0, 32);
}
function same(a: string, b: string) {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
const page = (body: string, status = 200) =>
  new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><body style="font:18px system-ui;max-width:32rem;margin:15vh auto;padding:0 1rem">${body}`,
    { status, headers: { "content-type": "text/html; charset=utf-8" } });

Deno.serve(async (req) => {
  const u = new URL(req.url);
  // GET only shows a confirm button: mail scanners that pre-open links must not record an answer. POST records it.
  const form = req.method === "POST" ? await req.formData() : null;
  const get = (k: string) => String(form ? form.get(k) ?? "" : u.searchParams.get(k) ?? "");
  const id = get("id"), o = get("o"), t = get("t");
  const el = get("l") !== "en";
  const secret = Deno.env.get("FOLLOWUP_SIGNING_SECRET") ?? "";
  if (!secret || !/^[0-9a-f-]{8,40}$/i.test(id) || !["ok", "worse"].includes(o) || !same(t, await token(id, o, secret))) {
    return page(el ? "Ο σύνδεσμος δεν είναι έγκυρος." : "This link is not valid.", 400);
  }
  if (!form) {
    const label = o === "ok" ? (el ? "Ναι, είναι καλύτερα" : "Yes, they're better") : (el ? "Όχι, είναι ακόμη άρρωστο ή χειρότερα" : "No, still unwell or worse");
    return page(`<form method="POST"><input type="hidden" name="id" value="${id}"><input type="hidden" name="o" value="${o}"><input type="hidden" name="t" value="${t}"><input type="hidden" name="l" value="${el ? "el" : "en"}">
      <p>${el ? "Επιβεβαίωσε την απάντησή σου:" : "Please confirm your answer:"}</p><button style="font:inherit;padding:.7rem 1.2rem">${label}</button></form>`);
  }
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { data } = await sb.from("followups").update({ outcome: o, outcome_at: new Date().toISOString() })
    .eq("id", id).is("outcome", null).select("species,level");
  if (data && data.length) {
    await sb.from("safety_events").insert({ kind: o === "ok" ? "outcome_ok" : "outcome_worse", species: data[0].species ?? "", floor_level: data[0].level ?? "" });
  }
  const app = Deno.env.get("APP_URL") ?? "";
  if (o === "worse") {
    return page(el
      ? `<h2>Λυπάμαι που ακούω ότι δεν είναι καλύτερα.</h2><p>Επικοινώνησε με κτηνίατρο <b>σήμερα</b>· αν υπάρχει δύσκολη αναπνοή, χλωμά ούλα, σπασμός, κατάρρευση ή αδυναμία ούρησης, πήγαινε αμέσως σε κτηνιατρείο.</p>${app ? `<p><a href="${app}">Νέος έλεγχος</a></p>` : ""}`
      : `<h2>Sorry to hear they're not better.</h2><p>Contact a vet <b>today</b>; with trouble breathing, pale gums, a seizure, collapse or inability to urinate, go to a clinic right away.</p>${app ? `<p><a href="${app}">New check</a></p>` : ""}`);
  }
  return page(el ? "<h2>Χαίρομαι που είναι καλύτερα! 🐾</h2><p>Ευχαριστούμε που μας το είπες.</p>" : "<h2>Glad they're doing better! 🐾</h2><p>Thanks for letting us know.</p>");
});
