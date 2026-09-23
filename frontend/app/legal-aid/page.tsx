import { redirect } from "next/navigation";

export default function LegalAidPage() {
  redirect("/app?tab=escalation");
}
