import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export type AlertRow = {
  alert_type: string;
  severity: string;
  message: string;
  related_entity: string | null;
  created_at: string;
};

export function AlertList({ rows }: { rows: AlertRow[] }) {
  if (!rows.length) return null;
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Type</TableHead>
          <TableHead>Severity</TableHead>
          <TableHead>Message</TableHead>
          <TableHead>Related</TableHead>
          <TableHead>At</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r, i) => (
          <TableRow key={i}>
            <TableCell>{r.alert_type}</TableCell>
            <TableCell>
              <Badge variant={r.severity === "high" || r.severity === "medium" ? "destructive" : "secondary"}>{r.severity}</Badge>
            </TableCell>
            <TableCell className="max-w-md">{r.message}</TableCell>
            <TableCell className="text-muted-foreground">{r.related_entity}</TableCell>
            <TableCell className="whitespace-nowrap text-xs text-muted-foreground">{r.created_at}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
