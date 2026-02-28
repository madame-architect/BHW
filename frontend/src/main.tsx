import React from "react";
import ReactDOM from "react-dom/client";
import { Alert, Box, Button, Container, FormControlLabel, LinearProgress, Paper, Radio, RadioGroup, Stack, Step, StepLabel, Stepper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import { acceptProposal, exportUrl, getDuplicates, mergeDuplicates, parseFile, rejectProposal, runPipeline } from "./api/client";
import { Item, Proposal } from "./types";

const steps = ["Upload", "Pipeline Review", "Duplicates", "Export"];

function App() {
  const [active, setActive] = React.useState(0);
  const [format, setFormat] = React.useState<"bib" | "rdf">("bib");
  const [sessionId, setSessionId] = React.useState<string>("");
  const [items, setItems] = React.useState<Item[]>([]);
  const [summary, setSummary] = React.useState<any>(null);
  const [runResult, setRunResult] = React.useState<any>(null);
  const [selectedItemId, setSelectedItemId] = React.useState<string>("");
  const [loading, setLoading] = React.useState(false);
  const [clusters, setClusters] = React.useState<any[]>([]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    const parsed = await parseFile(format, file);
    setSessionId(parsed.sessionId);
    setItems(parsed.items);
    setSummary(parsed.summary);
    setActive(1);
    setLoading(false);
  };

  const onRun = async () => {
    setLoading(true);
    const result = await runPipeline(sessionId);
    setRunResult(result);
    setLoading(false);
  };

  const proposals: Proposal[] = runResult?.proposals ?? [];
  const issues = runResult?.issues ?? [];
  const selectedItem = items.find((i) => i.id === selectedItemId);
  const selectedProposals = proposals.filter((p) => p.itemId === selectedItemId);

  const refreshDuplicates = async () => {
    const data = await getDuplicates(sessionId);
    setClusters(data.clusters || []);
  };

  return <Container sx={{ py: 4 }}>
    <Typography variant="h4" gutterBottom>Bibliography Hardening Workbench</Typography>
    <Stepper activeStep={active} sx={{ mb: 3 }}>{steps.map((s) => <Step key={s}><StepLabel>{s}</StepLabel></Step>)}</Stepper>
    {loading && <LinearProgress sx={{ mb: 2 }} />}

    {active === 0 && <Paper sx={{ p: 2 }}>
      <Typography>Choose input format and upload.</Typography>
      <RadioGroup row value={format} onChange={(e) => setFormat(e.target.value as "bib" | "rdf")}>
        <FormControlLabel value="bib" control={<Radio />} label="BibTeX (.bib)" />
        <FormControlLabel value="rdf" control={<Radio />} label="Zotero RDF (.rdf)" />
      </RadioGroup>
      <Button component="label" variant="contained">Upload file<input hidden type="file" onChange={onUpload} /></Button>
      {summary && <Alert severity="info" sx={{ mt: 2 }}>{summary.count} records parsed.</Alert>}
    </Paper>}

    {active === 1 && <Stack spacing={2}>
      <Button variant="contained" onClick={onRun}>Run Pipeline</Button>
      <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
        <Paper sx={{ p: 2, maxHeight: 380, overflow: "auto" }}>
          <Typography variant="h6">Items</Typography>
          <Table size="small"><TableHead><TableRow><TableCell>Key</TableCell><TableCell>Title</TableCell></TableRow></TableHead><TableBody>
            {items.map((it) => <TableRow key={it.id} hover selected={selectedItemId===it.id} onClick={() => setSelectedItemId(it.id)}><TableCell>{it.inputKey}</TableCell><TableCell>{it.title}</TableCell></TableRow>)}
          </TableBody></Table>
        </Paper>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6">Issues</Typography>
          {issues.map((i: any, idx: number) => <Alert key={idx} severity={i.severity === "error" ? "error" : "warning"}>{i.message}</Alert>)}
        </Paper>
      </Box>
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6">Diff panel {selectedItem?.inputKey}</Typography>
        {selectedProposals.map((p) => <Box key={p.id} sx={{ border: "1px solid #ddd", p:1, mb:1 }}>
          <Typography variant="body2">{p.stepId}: {p.rationale}</Typography>
          <pre>{JSON.stringify(p.patch, null, 2)}</pre>
          <Stack direction="row" spacing={1}>
            <Button size="small" onClick={() => acceptProposal(sessionId, p.id)}>Accept</Button>
            <Button size="small" color="error" onClick={() => rejectProposal(sessionId, p.id)}>Reject</Button>
          </Stack>
        </Box>)}
      </Paper>
      <Button onClick={() => {setActive(2); refreshDuplicates();}}>Next: Duplicates</Button>
    </Stack>}

    {active === 2 && <Paper sx={{ p: 2 }}>
      <Typography variant="h6">Duplicate Clusters</Typography>
      {clusters.map((c) => <Box key={c.id} sx={{ border: "1px solid #ddd", p:1, mb:1 }}>
        <Typography>{c.reason} ({c.confidence})</Typography>
        <Typography>{c.itemIds.join(", ")}</Typography>
        <Button size="small" onClick={() => mergeDuplicates(sessionId, { canonicalItemId: c.itemIds[0], mergeItemIds: c.itemIds.slice(1), fieldOverrides: {} })}>Auto-merge to first</Button>
      </Box>)}
      <Button onClick={() => setActive(3)}>Next: Export</Button>
    </Paper>}

    {active === 3 && <Paper sx={{ p: 2 }}>
      <Typography variant="h6">Exports</Typography>
      <Stack direction="row" spacing={1}>
        <Button href={exportUrl(sessionId, format)} target="_blank">Cleaned {format.toUpperCase()}</Button>
        <Button href={exportUrl(sessionId, "audit")} target="_blank">Audit JSON</Button>
        <Button href={exportUrl(sessionId, "csv")} target="_blank">CSV table</Button>
        <Button href={exportUrl(sessionId, "md")} target="_blank">Markdown table</Button>
      </Stack>
    </Paper>}
  </Container>;
}

ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
