export type NavItem = {
  href: string;
  label: string;
  icon?: string;
};

export type ImportLogEntry = {
  at: string;
  fileName: string;
  statementType: string;
  companyName?: string;
  importedCount?: number;
  rejectedCount?: number;
};
