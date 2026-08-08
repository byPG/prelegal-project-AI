import { Document, Page, StyleSheet, Text, View } from "@react-pdf/renderer";
import {
  MUTUAL_NDA_ATTRIBUTION,
  MUTUAL_NDA_CLAUSES,
  type ContentSegment,
} from "@/lib/mutual-nda-content";
import { formatLegalDate } from "@/lib/format";
import type { MutualNdaFormData } from "@/types/mutual-nda";

const COLOR = {
  ink: "#1c2a22",
  inkSoft: "#4a5a4d",
  ledgerDark: "#1e3823",
  rule: "#9b3b3b",
  ruleFaint: "#c9a4a4",
  brass: "#ad8a52",
  line: "#c9c0a8",
  parchment: "#f8f4ea",
};

const styles = StyleSheet.create({
  page: {
    backgroundColor: COLOR.parchment,
    color: COLOR.ink,
    fontFamily: "Times-Roman",
    fontSize: 10.5,
    lineHeight: 1.5,
    paddingTop: 54,
    paddingBottom: 54,
    paddingLeft: 68,
    paddingRight: 52,
  },
  ruledColumn: {
    marginLeft: -28,
    paddingLeft: 27,
    borderLeftWidth: 1,
    borderLeftColor: COLOR.rule,
  },
  header: {
    marginBottom: 22,
    alignItems: "center",
  },
  eyebrow: {
    fontFamily: "Helvetica",
    fontSize: 8,
    letterSpacing: 2.4,
    color: COLOR.brass,
  },
  title: {
    fontFamily: "Times-Bold",
    fontSize: 20,
    marginTop: 6,
  },
  partiesRow: {
    flexDirection: "row",
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: COLOR.line,
    paddingVertical: 14,
    marginBottom: 18,
  },
  partyCol: {
    flex: 1,
    paddingRight: 12,
  },
  sectionLabel: {
    fontFamily: "Helvetica",
    fontSize: 7.5,
    letterSpacing: 1.6,
    color: COLOR.inkSoft,
    marginBottom: 6,
  },
  field: {
    marginBottom: 8,
  },
  fieldLabel: {
    fontFamily: "Helvetica",
    fontSize: 7,
    letterSpacing: 1.2,
    color: COLOR.brass,
    marginBottom: 2,
  },
  fieldValue: {
    fontFamily: "Times-Roman",
    fontSize: 10,
  },
  fieldValueEmpty: {
    fontFamily: "Times-Italic",
    fontSize: 10,
    color: COLOR.inkSoft,
  },
  termsGrid: {
    marginBottom: 24,
  },
  termsRow: {
    flexDirection: "row",
    marginBottom: 8,
  },
  termsRowCol: {
    flex: 1,
    paddingRight: 12,
  },
  standardTermsHeading: {
    fontFamily: "Times-Bold",
    fontSize: 13,
    marginBottom: 14,
  },
  clause: {
    marginBottom: 11,
    flexDirection: "row",
  },
  clauseNumberCol: {
    width: 18,
  },
  clauseNumber: {
    fontFamily: "Helvetica",
    fontSize: 9,
    color: COLOR.brass,
  },
  clauseBody: {
    flex: 1,
    textAlign: "justify",
  },
  clauseTitle: {
    fontFamily: "Times-Bold",
  },
  fieldInline: {
    color: COLOR.ledgerDark,
  },
  fieldInlineEmpty: {
    fontFamily: "Times-Italic",
    color: COLOR.inkSoft,
  },
  footer: {
    position: "absolute",
    bottom: 28,
    left: 68,
    right: 52,
    fontFamily: "Helvetica-Oblique",
    fontSize: 7.5,
    color: COLOR.inkSoft,
    borderTopWidth: 1,
    borderColor: COLOR.line,
    paddingTop: 8,
  },
});

function fieldDisplayValue(formData: MutualNdaFormData, field: keyof MutualNdaFormData) {
  const raw = formData[field];
  if (!raw) return "";
  return field === "effectiveDate" ? formatLegalDate(raw) : raw;
}

function PdfField({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label.toUpperCase()}</Text>
      <Text style={value ? styles.fieldValue : styles.fieldValueEmpty}>{value || "—"}</Text>
    </View>
  );
}

function ClauseSegment({
  segment,
  formData,
}: {
  segment: ContentSegment;
  formData: MutualNdaFormData;
}) {
  if (segment.type === "text") {
    return <Text style={segment.bold ? styles.clauseTitle : undefined}>{segment.value}</Text>;
  }
  const value = fieldDisplayValue(formData, segment.field);
  if (value) {
    return <Text style={styles.fieldInline}>{value}</Text>;
  }
  return <Text style={styles.fieldInlineEmpty}>{segment.fallback}</Text>;
}

export function MutualNdaPdfDocument({ formData }: { formData: MutualNdaFormData }) {
  return (
    <Document title="Mutual Non-Disclosure Agreement">
      <Page size="A4" style={styles.page}>
        <View style={styles.ruledColumn}>
          <View style={styles.header}>
            <Text style={styles.eyebrow}>COVER PAGE</Text>
            <Text style={styles.title}>Mutual Non-Disclosure Agreement</Text>
          </View>

          <View style={styles.partiesRow}>
            <View style={styles.partyCol}>
              <Text style={styles.sectionLabel}>PARTY ONE</Text>
              <PdfField label="Legal Name" value={formData.partyOneName} />
              <PdfField label="Address" value={formData.partyOneAddress} />
            </View>
            <View style={styles.partyCol}>
              <Text style={styles.sectionLabel}>PARTY TWO</Text>
              <PdfField label="Legal Name" value={formData.partyTwoName} />
              <PdfField label="Address" value={formData.partyTwoAddress} />
            </View>
          </View>

          <View style={styles.termsGrid}>
            <PdfField label="Purpose" value={formData.purpose} />
            <View style={styles.termsRow}>
              <View style={styles.termsRowCol}>
                <PdfField
                  label="Effective Date"
                  value={fieldDisplayValue(formData, "effectiveDate")}
                />
              </View>
              <View style={styles.termsRowCol}>
                <PdfField label="MNDA Term" value={formData.mndaTerm} />
              </View>
            </View>
            <View style={styles.termsRow}>
              <View style={styles.termsRowCol}>
                <PdfField
                  label="Term of Confidentiality"
                  value={formData.termOfConfidentiality}
                />
              </View>
              <View style={styles.termsRowCol}>
                <PdfField label="Governing Law" value={formData.governingLaw} />
              </View>
            </View>
            <PdfField label="Jurisdiction" value={formData.jurisdiction} />
          </View>

          <Text style={styles.standardTermsHeading}>Standard Terms</Text>

          {MUTUAL_NDA_CLAUSES.map((clause) => (
            <View key={clause.number} style={styles.clause} wrap={false}>
              <View style={styles.clauseNumberCol}>
                <Text style={styles.clauseNumber}>{clause.number}.</Text>
              </View>
              <Text style={styles.clauseBody}>
                <Text style={styles.clauseTitle}>{clause.title}. </Text>
                {clause.segments.map((segment, index) => (
                  <ClauseSegment key={index} segment={segment} formData={formData} />
                ))}
              </Text>
            </View>
          ))}
        </View>

        <Text style={styles.footer} fixed>
          {MUTUAL_NDA_ATTRIBUTION}
        </Text>
      </Page>
    </Document>
  );
}
