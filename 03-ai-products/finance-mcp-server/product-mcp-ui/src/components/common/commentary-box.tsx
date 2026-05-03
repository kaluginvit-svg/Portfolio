import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function CommentaryBox({ text }: { text: string }) {
  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Commentary</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm leading-relaxed text-foreground/90">{text}</p>
      </CardContent>
    </Card>
  );
}
