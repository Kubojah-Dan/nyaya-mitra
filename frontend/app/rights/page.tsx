import { redirect } from "next/navigation";

export default function RightsPage() {
  redirect("/app?tab=rights");
}
