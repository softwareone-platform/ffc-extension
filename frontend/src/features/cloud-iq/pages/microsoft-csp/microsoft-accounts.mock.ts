export type MicrosoftAccount = {
  id: string;
  name: string;
  microsoftId: string;
  domainName: string;
};

export const microsoftAccounts: MicrosoftAccount[] = [
  {
    id: "1",
    name: "A J Betonghåltagning AB",
    microsoftId: "08b4913c-cb23-450f-9581-fcf3888777dc",
    domainName: "ajbab.onmicrosoft.com",
  },
  {
    id: "2",
    name: "AB Toolpal",
    microsoftId: "c1ed8084-9604-47e3-ab3d-d8d15a00680f",
    domainName: "abtoolpal.onmicrosoft.com",
  },
  {
    id: "3",
    name: "Addoceo AB",
    microsoftId: "e38e4801-7f80-441c-b29e-4049ac9ee3c8",
    domainName: "addoceo.se",
  },
  {
    id: "4",
    name: "Advokat Tore Wiwen-Nilsson",
    microsoftId: "a76a3f47-055b-46c0-a999-233f11ed3bca",
    domainName: "indarb.onmicrosoft.com",
  },
  {
    id: "5",
    name: "Aelias Revision AB",
    microsoftId: "d2553447-7395-49d3-999d-de5d36b9b6ff",
    domainName: "aeliasrevision.onmicrosoft.com",
  },
  {
    id: "6",
    name: "Aiolos Medical AB",
    microsoftId: "28a7260a-829d-4e63-b4ed-02586aaae709",
    domainName: "aiolosmedical.onmicrosoft.com",
  },
  {
    id: "7",
    name: "Air 4 You Sweden AB",
    microsoftId: "31843165-878b-477b-bcf0-428fc8c1f1d4",
    domainName: "air4you.se",
  },
];

export const accountFilterOptions = [
  { label: "Consumer", value: "consumer" },
  { label: "Nethouse Sverige AB", value: "nethouse-sverige-ab" },
  { label: "End customer of Nethouse Sverige AB", value: "end-customer-of-nethouse-sverige-ab" },
];
