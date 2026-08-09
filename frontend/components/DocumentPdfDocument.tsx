import { Document, Page, StyleSheet, Text, View } from "@react-pdf/renderer";
import { computeMarkers } from "@/lib/document-numbering";
import type { DocumentTemplate, InlineSegment } from "@/types/document";

const COLOR = {
  ink: "#1c2a22",
  inkSoft: "#4a5a4d",
  ledgerDark: "#1e3823",
  rule: "#9b3b3b",
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
    textAlign: "center",
  },
  fieldsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: COLOR.line,
    paddingVertical: 14,
    marginBottom: 24,
  },
  field: {
    width: "50%",
    marginBottom: 8,
    paddingRight: 12,
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
    width: 24,
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
  bold: {
    fontFamily: "Times-Bold",
  },
  header2: {
    fontFamily: "Times-Bold",
    fontSize: 11.5,
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

function PdfField({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label.toUpperCase()}</Text>
      <Text style={value ? styles.fieldValue : styles.fieldValueEmpty}>{value || "—"}</Text>
    </View>
  );
}

function PdfInlineSegment({
  segment,
  template,
  fields,
}: {
  segment: InlineSegment;
  template: DocumentTemplate;
  fields: Record<string, string>;
}) {
  if (segment.type === "text") {
    const style = segment.variant === "header2" ? styles.header2 : segment.variant === "bold" || segment.variant === "header3" ? styles.bold : undefined;
    return <Text style={style}>{segment.text}</Text>;
  }

  if (segment.type === "link") {
    return <Text>{segment.text}</Text>;
  }

  const value = fields[segment.field_key]?.trim() ?? "";
  if (value) {
    return <Text style={styles.fieldInline}>{value}</Text>;
  }
  const field = template.fields.find((candidate) => candidate.key === segment.field_key);
  return <Text style={styles.fieldInlineEmpty}>[{field?.label ?? segment.field_key}]</Text>;
}

export function DocumentPdfDocument({
  template,
  fields,
}: {
  template: DocumentTemplate;
  fields: Record<string, string>;
}) {
  const markers = computeMarkers(template.body);

  return (
    <Document title={template.name}>
      <Page size="A4" style={styles.page}>
        <View style={styles.ruledColumn}>
          <View style={styles.header}>
            <Text style={styles.eyebrow}>COVER PAGE</Text>
            <Text style={styles.title}>{template.name}</Text>
          </View>

          <View style={styles.fieldsGrid}>
            {template.fields.map((field) => (
              <PdfField key={field.key} label={field.label} value={fields[field.key]?.trim() ?? ""} />
            ))}
          </View>

          <Text style={styles.standardTermsHeading}>Standard Terms</Text>

          {template.body.map((item, index) => (
            <View key={index} style={[styles.clause, { paddingLeft: item.depth * 14 }]} wrap={false}>
              <View style={styles.clauseNumberCol}>
                <Text style={styles.clauseNumber}>{markers[index]}</Text>
              </View>
              <Text style={styles.clauseBody}>
                {item.inline.map((segment, segIndex) => (
                  <PdfInlineSegment key={segIndex} segment={segment} template={template} fields={fields} />
                ))}
              </Text>
            </View>
          ))}
        </View>

        {template.attribution && (
          <Text style={styles.footer} fixed>
            {template.attribution}
          </Text>
        )}
      </Page>
    </Document>
  );
}
