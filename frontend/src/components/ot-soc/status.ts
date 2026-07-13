import type { OtCase } from "@/lib/otSocApi";

export function classificationLabel(classification: OtCase["classification"] | string) {
  const labels: Record<string, string> = {
    validation_not_malicious: "Validation",
    important_ot_operation: "Important",
    suspicious_ot_operation: "Suspicious",
  };

  return labels[classification] || classification;
}

export function classificationBadge(classification: OtCase["classification"] | string) {
  if (classification === "suspicious_ot_operation") {
    return "border-[#ff5a2f]/60 bg-[#ff5a2f]/15 text-[#ff7a52]";
  }
  if (classification === "important_ot_operation") {
    return "border-[#eab308]/50 bg-[#eab308]/12 text-[#facc15]";
  }
  return "border-[#36d399]/45 bg-[#36d399]/12 text-[#6ee7b7]";
}

export function criticalityBadge(criticality: string) {
  if (criticality === "high") {
    return "border-[#ff5a2f]/60 bg-[#ff5a2f]/15 text-[#ff7a52]";
  }
  if (criticality === "medium") {
    return "border-[#eab308]/50 bg-[#eab308]/12 text-[#facc15]";
  }
  return "border-white/15 bg-white/[0.04] text-white/65";
}
