export interface MutualNdaFormData {
  partyOneName: string;
  partyOneAddress: string;
  partyTwoName: string;
  partyTwoAddress: string;
  purpose: string;
  effectiveDate: string;
  mndaTerm: string;
  termOfConfidentiality: string;
  governingLaw: string;
  jurisdiction: string;
}

export const BLANK_MUTUAL_NDA_FORM_DATA: MutualNdaFormData = {
  partyOneName: "",
  partyOneAddress: "",
  partyTwoName: "",
  partyTwoAddress: "",
  purpose: "",
  effectiveDate: "",
  mndaTerm: "2 years",
  termOfConfidentiality: "3 years",
  governingLaw: "",
  jurisdiction: "",
};

export interface MutualNdaFieldConfig {
  key: keyof MutualNdaFormData;
  label: string;
  placeholder: string;
  type: "text" | "date" | "textarea";
  group: "party-one" | "party-two" | "terms";
}

export const MUTUAL_NDA_FIELDS: MutualNdaFieldConfig[] = [
  {
    key: "partyOneName",
    label: "Legal name",
    placeholder: "Acme, Inc.",
    type: "text",
    group: "party-one",
  },
  {
    key: "partyOneAddress",
    label: "Address",
    placeholder: "123 Market Street, San Francisco, CA 94105",
    type: "text",
    group: "party-one",
  },
  {
    key: "partyTwoName",
    label: "Legal name",
    placeholder: "Beta Labs LLC",
    type: "text",
    group: "party-two",
  },
  {
    key: "partyTwoAddress",
    label: "Address",
    placeholder: "456 Harbor Way, Austin, TX 78701",
    type: "text",
    group: "party-two",
  },
  {
    key: "purpose",
    label: "Purpose",
    placeholder: "evaluating a potential business relationship between the parties",
    type: "textarea",
    group: "terms",
  },
  {
    key: "effectiveDate",
    label: "Effective date",
    placeholder: "",
    type: "date",
    group: "terms",
  },
  {
    key: "mndaTerm",
    label: "MNDA term",
    placeholder: "2 years",
    type: "text",
    group: "terms",
  },
  {
    key: "termOfConfidentiality",
    label: "Term of confidentiality",
    placeholder: "3 years",
    type: "text",
    group: "terms",
  },
  {
    key: "governingLaw",
    label: "Governing law",
    placeholder: "Delaware",
    type: "text",
    group: "terms",
  },
  {
    key: "jurisdiction",
    label: "Jurisdiction",
    placeholder: "New Castle County, Delaware",
    type: "text",
    group: "terms",
  },
];
