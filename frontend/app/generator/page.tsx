import { redirect } from "next/navigation";

export default function GeneratorPage() {
  redirect("/app?tab=generator");
}
