import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AiSignalView } from "@/components/ai-signal-view";

export default async function AiSignalPage() {
  const store = await cookies();
  if (!store.get("tabdeal_panel_session")?.value) redirect("/login");
  return <AiSignalView />;
}
