"use client";

import { useState, useEffect, useRef, FormEvent, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import KnowledgeOrb from "@/components/KnowledgeOrb";
import { Upload, Sparkles, Image as ImageIcon, FileText, ArrowLeft, CheckCircle2, AlertCircle, HelpCircle, Send, Loader2, BookOpen, X, Download } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://notes-up.onrender.com";

interface Topic {
  topic: string;
  summary: string;
  status?: string;
  why_needed?: string;
  student_knowledge?: string;
  missing_information?: string[];
}

interface FacultyTopic {
  topic: string;
  description: string;
  importance: string;
  page_reference?: string;
}

interface AnalysisResults {
  faculty_knowledge_map?: FacultyTopic[];
  missing_topics?: Topic[];
  partially_covered_topics?: Topic[];
  covered_topics?: string[];
  _faculty_raw?: unknown;
}

interface NoteSection {
  heading: string;
  content: string;
  equations?: string[];
}

interface GeneratedNote {
  topic?: string;
  status?: string;
  why_needed?: string;
  student_knowledge?: string;
  missing_information?: string[];
  sections?: NoteSection[];
  exam_points?: string[];
  sources?: string[];
}

interface ActiveNotes {
  topic: string;
  content: GeneratedNote | GeneratedNote[];
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function cleanGeneratedText(value: unknown): string {
  if (typeof value !== "string") return "";
  return value
    .replace(/\\\\/g, " ")
    .replace(/\\\(/g, "")
    .replace(/\\\)/g, "")
    .replace(/\\\[/g, "")
    .replace(/\\\]/g, "")
    .replace(/\\(?=\s|$)/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function renderNoteText(value: unknown) {
  const text = cleanGeneratedText(value);
  if (!text) return null;

  return text.split(/\n\n+/).map((paragraph, index) => (
    <p key={index} className="text-gray-300 leading-7 whitespace-pre-wrap mb-4 last:mb-0">
      {paragraph}
    </p>
  ));
}

declare global {
  interface Window {
    katex?: {
      render: (
        expression: string,
        element: HTMLElement,
        options?: {
          displayMode?: boolean;
          throwOnError?: boolean;
          strict?: "ignore" | "warn" | "error";
        }
      ) => void;
    };
  }
}

let katexLoader: Promise<void> | null = null;

function loadKatex() {
  if (typeof window === "undefined") return Promise.resolve();

  if (window.katex) return Promise.resolve();

  if (katexLoader) return katexLoader;

  katexLoader = new Promise<void>((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>(
      'script[data-katex="true"]'
    );

    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(), { once: true });
      existingScript.addEventListener("error", () => reject(new Error("KaTeX failed to load")), { once: true });
      return;
    }

    if (!document.querySelector('link[data-katex="true"]')) {
      const stylesheet = document.createElement("link");
      stylesheet.rel = "stylesheet";
      stylesheet.href = "https://cdn.jsdelivr.net/npm/katex@0.18.9/dist/katex.min.css";
      stylesheet.dataset.katex = "true";
      document.head.appendChild(stylesheet);
    }

    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/katex@0.18.9/dist/katex.min.js";
    script.async = true;
    script.dataset.katex = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("KaTeX failed to load"));
    document.head.appendChild(script);
  });

  return katexLoader;
}

type JsPdfApi = {
  jsPDF: new () => {
    internal: {
      pageSize: {
        getWidth: () => number;
        getHeight: () => number;
      };
    };
    setFont: (family: string, style?: string) => void;
    setFontSize: (size: number) => void;
    splitTextToSize: (text: string, maxWidth: number) => string[];
    text: (text: string | string[], x: number, y: number) => void;
    addPage: () => void;
    save: (filename: string) => void;
  };
};

let jsPdfLoader: Promise<JsPdfApi> | null = null;

function loadJsPdf(): Promise<JsPdfApi> {
  if (typeof window === "undefined") return Promise.reject(new Error("PDF export requires a browser."));
  if ((window as Window & { jspdf?: JsPdfApi }).jspdf) return Promise.resolve((window as Window & { jspdf?: JsPdfApi }).jspdf!);
  if (jsPdfLoader) return jsPdfLoader;

  jsPdfLoader = new Promise<JsPdfApi>((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>('script[data-jspdf="true"]');

    if (existingScript) {
      existingScript.addEventListener("load", () => {
        const api = (window as Window & { jspdf?: JsPdfApi }).jspdf;
        api ? resolve(api) : reject(new Error("jsPDF failed to initialize"));
      }, { once: true });
      existingScript.addEventListener("error", () => reject(new Error("jsPDF failed to load")), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/jspdf@4.2.0/dist/jspdf.umd.min.js";
    script.async = true;
    script.dataset.jspdf = "true";
    script.onload = () => {
      const api = (window as Window & { jspdf?: JsPdfApi }).jspdf;
      api ? resolve(api) : reject(new Error("jsPDF failed to initialize"));
    };
    script.onerror = () => reject(new Error("jsPDF failed to load"));
    document.head.appendChild(script);
  });

  return jsPdfLoader;
}

function KatexEquation({ value }: { value: unknown }) {
  const equation = cleanGeneratedText(value);
  const equationRef = useRef<HTMLDivElement>(null);
  const [katexError, setKatexError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    if (!equation || !equationRef.current) return;

    setKatexError(false);

    loadKatex()
      .then(() => {
        if (cancelled || !equationRef.current || !window.katex) return;

        try {
          window.katex.render(equation, equationRef.current, {
            displayMode: true,
            throwOnError: false,
            strict: "ignore",
          });
        } catch (error) {
          console.error("KaTeX rendering error:", error);
          if (!cancelled) setKatexError(true);
        }
      })
      .catch((error) => {
        console.error("KaTeX loading error:", error);
        if (!cancelled) setKatexError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [equation]);

  if (!equation) return null;

  return (
    <div className="my-4 rounded-2xl border border-blue-500/20 bg-blue-500/[0.04] px-6 py-5 text-center">
      <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.25em] text-blue-400">Equation</div>
      <div
        ref={equationRef}
        className="overflow-x-auto text-base md:text-lg text-blue-100 leading-relaxed min-h-8"
        aria-label={`Mathematical equation: ${equation}`}
      >
        {katexError ? (
          <code className="font-mono text-blue-200 whitespace-pre-wrap">{equation}</code>
        ) : null}
      </div>
    </div>
  );
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [facultyRaw, setFacultyRaw] = useState<unknown>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [activeNotes, setActiveNotes] = useState<ActiveNotes | null>(null);
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [facultyFile, setFacultyFile] = useState<File | null>(null);
  const [studentImages, setStudentImages] = useState<File[]>([]);

  useEffect(() => {
  try {
    const savedChat = localStorage.getItem("ss_last_chat");
    const savedRaw = localStorage.getItem("ss_faculty_raw");

    if (savedChat && savedChat !== "undefined") {
      setChatHistory(JSON.parse(savedChat));
    }

    if (savedRaw && savedRaw !== "undefined") {
      setFacultyRaw(JSON.parse(savedRaw));
    }

    localStorage.removeItem("ss_last_results");
  } catch (e) {
    console.error("LocalStorage Error:", e);
  }
  }, []);

  const handleFacultyFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFacultyFile(e.target.files?.[0] || null);
  };

  const handleStudentImagesChange = (e: ChangeEvent<HTMLInputElement>) => {
    setStudentImages(e.target.files ? Array.from(e.target.files) : []);
  };

  const handleAnalyze = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!facultyFile) {
      alert("Please upload the faculty material first.");
      return;
    }

    if (studentImages.length === 0) {
      alert("Please upload at least one handwritten note image.");
      return;
    }

    setLoading(true);

    const steps = [
      "Reading faculty materials...",
      "Transcribing handwritten notes...",
      "Mapping course knowledge...",
      "Analyzing conceptual gaps...",
      "Generating your report...",
    ];

    let stepIdx = 0;
    setLoadingStatus(steps[0]);

    const interval = setInterval(() => {
      stepIdx++;
      if (stepIdx < steps.length) setLoadingStatus(steps[stepIdx]);
    }, 1500);

    const formData = new FormData();
    formData.append("faculty_file", facultyFile);
    studentImages.forEach((img) => formData.append("student_images", img));

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Analysis failed with status ${response.status}`);
      }

      const data: AnalysisResults = await response.json();

      setFacultyRaw(data._faculty_raw || null);

      if (data._faculty_raw) {
        localStorage.setItem("ss_faculty_raw", JSON.stringify(data._faculty_raw));
      }

      setResults(data);
      localStorage.setItem("ss_last_results", JSON.stringify(data));
      setChatHistory([]);
      localStorage.setItem("ss_last_chat", JSON.stringify([]));
    } catch (error) {
      console.error("Analysis Error:", error);
      alert("Analysis failed: " + (error instanceof Error ? error.message : "Unknown error"));
    } finally {
      clearInterval(interval);
      setLoading(false);
      setLoadingStatus("");
    }
  };

  const generateNotes = async (topic?: Topic, isAll = false) => {
    const id = isAll ? "all" : topic?.topic || "";
    if (!isAll && !topic) return;

    try {
      let currentFacultyData = facultyRaw;

      if (!currentFacultyData) {
        const savedRaw = localStorage.getItem("ss_faculty_raw");
        if (savedRaw && savedRaw !== "undefined") currentFacultyData = JSON.parse(savedRaw);
      }

      const missingTopics = Array.isArray(results?.missing_topics)
        ? results.missing_topics.filter((item) => item && typeof item === "object")
        : [];

      const partialTopics = Array.isArray(results?.partially_covered_topics)
        ? results.partially_covered_topics.filter((item) => item && typeof item === "object")
        : [];

      const allTopics = [...missingTopics, ...partialTopics];

      if (isAll && allTopics.length === 0) {
        throw new Error("No missing or partially covered topics were found.");
      }

      setGeneratingId(id);

      let body;

      if (isAll) {
        body = {
          topic: "All Missing and Partially Covered Topics",
          status: "missing",
          why_needed: "These topics were identified by the gap analysis as missing or only partially covered in the student's notes.",
          student_knowledge: allTopics.map((item) => `${item.topic}: ${item.student_knowledge || "Not sufficiently covered"}`).join("\n"),
          missing_information: allTopics.flatMap((item) => item.missing_information || [item.summary || ""]),
          all_gaps: allTopics,
          faculty_context: JSON.stringify(results?.faculty_knowledge_map || currentFacultyData || ""),
        };
      } else {
        body = {
          topic: topic?.topic || "",
          status: topic?.status || (missingTopics.some((item) => item.topic === topic?.topic) ? "missing" : "partially_covered"),
          why_needed: topic?.why_needed || topic?.summary || "",
          student_knowledge: topic?.student_knowledge || "",
          missing_information: topic?.missing_information || [topic?.summary || ""],
          faculty_context: JSON.stringify(results?.faculty_knowledge_map || currentFacultyData || ""),
        };
      }

      console.log("GENERATE NOTES REQUEST", {
        isAll,
        topic: isAll ? "ALL" : topic?.topic,
        gapCount: allTopics.length,
        apiUrl: API_URL,
      });

      const response = await fetch(`${API_URL}/generate-notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server Error (${response.status}): ${errorText}`);
      }

      const data: GeneratedNote | GeneratedNote[] = await response.json();

      setActiveNotes({
        topic: isAll ? "All Gaps Study Guide" : topic?.topic || "Study Notes",
        content: data,
      });
    } catch (error) {
      console.error("Generation Error:", error);
      alert("Failed to generate notes: " + (error instanceof Error ? error.message : "Unknown error"));
    } finally {
      setGeneratingId(null);
    }
  };

  const buildDownloadText = (notes: ActiveNotes) => {
    const noteList = Array.isArray(notes.content) ? notes.content : [notes.content];
    const lines: string[] = [
      notes.topic,
      "",
      "Generated by Note'sUp — AI Study Guide",
      "",
    ];

    noteList.forEach((note, index) => {
      lines.push(`${index + 1}. ${note.topic || "Study Topic"}`, "");

      if (note.status) lines.push(`Status: ${note.status}`, "");
      if (note.why_needed) lines.push("Why this is needed", cleanGeneratedText(note.why_needed), "");
      if (note.student_knowledge) lines.push("What you already know", cleanGeneratedText(note.student_knowledge), "");

      if (note.missing_information?.length) {
        lines.push("Focus on these gaps", "");
        note.missing_information.forEach((item) => lines.push("• " + cleanGeneratedText(item)));
        lines.push("");
      }

      note.sections?.forEach((section) => {
        lines.push(cleanGeneratedText(section.heading), "", cleanGeneratedText(section.content), "");
        section.equations?.forEach((equation) => {
          lines.push("Equation:", cleanGeneratedText(equation), "");
        });
      });

      if (note.exam_points?.length) {
        lines.push("Exam Points", "");
        note.exam_points.forEach((point) => lines.push("• " + cleanGeneratedText(point)));
        lines.push("");
      }

      if (note.sources?.length) {
        lines.push("Sources: " + note.sources.map((source) => cleanGeneratedText(source)).join(" • "), "");
      }

      lines.push("────────────────────────────────────────", "");
    });

    return lines.join("\n");
  };

  const downloadNotesTxt = (notes: ActiveNotes) => {
    const blob = new Blob([buildDownloadText(notes)], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "notes-up-study-guide.txt";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  const downloadNotesPdf = async (notes: ActiveNotes) => {
    try {
      const jsPdf = await loadJsPdf();
      const doc = new jsPdf.jsPDF();
      const margin = 18;
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const usableWidth = pageWidth - margin * 2;
      let y = margin;

      const addText = (text: string, size = 11, bold = false) => {
        doc.setFont("helvetica", bold ? "bold" : "normal");
        doc.setFontSize(size);

        const chunks = doc.splitTextToSize(text || " ", usableWidth);
        const lineHeight = size * 0.48;

        if (y + chunks.length * lineHeight > pageHeight - margin) {
          doc.addPage();
          y = margin;
        }

        doc.text(chunks, margin, y);
        y += chunks.length * lineHeight + 5;
      };

      addText(notes.topic, 18, true);
      addText("Generated by Note'sUp — AI Study Guide", 10);
      y += 3;

      const noteList = Array.isArray(notes.content) ? notes.content : [notes.content];

      noteList.forEach((note, index) => {
        addText(`${index + 1}. ${note.topic || "Study Topic"}`, 15, true);

        if (note.status) addText(`Status: ${note.status}`, 10, true);
        if (note.why_needed) {
          addText("Why this is needed", 12, true);
          addText(cleanGeneratedText(note.why_needed));
        }
        if (note.student_knowledge) {
          addText("What you already know", 12, true);
          addText(cleanGeneratedText(note.student_knowledge));
        }

        if (note.missing_information?.length) {
          addText("Focus on these gaps", 12, true);
          note.missing_information.forEach((item) => addText("• " + cleanGeneratedText(item)));
        }

        note.sections?.forEach((section) => {
          addText(cleanGeneratedText(section.heading), 12, true);
          addText(cleanGeneratedText(section.content));
          section.equations?.forEach((equation) => addText("Equation: " + cleanGeneratedText(equation), 10));
        });

        if (note.exam_points?.length) {
          addText("Exam Points", 12, true);
          note.exam_points.forEach((point) => addText("• " + cleanGeneratedText(point)));
        }

        if (note.sources?.length) {
          addText("Sources: " + note.sources.map((source) => cleanGeneratedText(source)).join(" • "), 9);
        }

        y += 5;
      });

      doc.save("notes-up-study-guide.pdf");
    } catch (error) {
      console.error("PDF generation error:", error);
      alert("Could not generate the PDF. Please try the TXT option instead.");
    }
  };

  const handleChat = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!chatInput.trim()) return;

    const question = chatInput.trim();
    const userMsg: ChatMessage = { role: "user", content: question };
    const newHist = [...chatHistory, userMsg];

    setChatHistory(newHist);
    setChatInput("");

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          notes: JSON.stringify(results || {}),
          question,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Chat failed with status ${response.status}`);
      }

      const data = await response.json();
      const finalHist: ChatMessage[] = [
        ...newHist,
        { role: "assistant", content: data.answer || "I couldn't generate an answer." },
      ];

      setChatHistory(finalHist);
      localStorage.setItem("ss_last_chat", JSON.stringify(finalHist));
    } catch (error) {
      console.error("Chat Error:", error);

      setChatHistory([
        ...newHist,
        {
          role: "assistant",
          content: `Error: ${error instanceof Error ? error.message : "Unable to contact the study assistant."}`,
        },
      ]);
    }
  };

  const resetAnalysis = () => {
    setResults(null);
    setFacultyRaw(null);
    setActiveNotes(null);
    setChatHistory([]);
    localStorage.removeItem("ss_last_results");
    localStorage.removeItem("ss_last_chat");
    localStorage.removeItem("ss_faculty_raw");
  };

  return (
    <main className="min-h-screen bg-black text-white font-sans selection:bg-blue-500/30">
      <nav className="fixed top-0 w-full z-50 px-6 py-4 flex justify-between items-center backdrop-blur-sm bg-black/20">
        <div className="flex items-center gap-2 font-medium tracking-tighter text-lg">
          <span className="text-blue-500">✦</span>
          <span>Note&apos;sUp</span>
        </div>
        <div className="text-xs uppercase tracking-widest text-gray-500 font-medium">AI Gap Analyzer v1.0</div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 pt-32 pb-24">
        <div className="text-center mb-20">
          <div className="inline-block px-3 py-1 mb-6 text-xs font-medium tracking-wider text-blue-400 uppercase border border-blue-500/30 rounded-full bg-blue-500/10">
            The Future of Learning
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-6 bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent">
            Compare. Analyze.
            <br />
            Bridge the Gap.
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
            Upload your faculty materials and handwritten notes. Our AI identifies exactly what you&apos;ve mastered and what you&apos;re missing.
          </p>
        </div>

        <div className="flex justify-center mb-24 relative">
          <div className="absolute inset-0 bg-blue-600/20 blur-[120px] rounded-full w-64 h-64 mx-auto" />
          <div className="relative z-10 scale-110">
            <KnowledgeOrb />
          </div>
        </div>

        {!results ? (
          <form onSubmit={handleAnalyze} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-8 flex flex-col justify-between group">
              <div className="flex items-center gap-3 mb-6 text-gray-400 group-hover:text-white transition-colors">
                <FileText size={20} className="text-blue-500" />
                <span className="font-medium">Faculty Material</span>
              </div>

              <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-white/[0.02] border border-white/[0.05] group-hover:bg-white/[0.05] transition-all">
                <Upload className="text-gray-600 mb-3 group-hover:text-gray-400 transition-colors" size={24} />
                <input
                  type="file"
                  accept=".pdf,.pptx"
                  onChange={handleFacultyFileChange}
                  className="text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                />
              </div>
            </div>

            <div className="glass-card p-8 flex flex-col justify-between group">
              <div className="flex items-center gap-3 mb-6 text-gray-400 group-hover:text-white transition-colors">
                <ImageIcon size={20} className="text-blue-500" />
                <span className="font-medium">Handwritten Notes</span>
              </div>

              <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-white/[0.02] border border-white/[0.05] group-hover:bg-white/[0.05] transition-all">
                <ImageIcon className="text-gray-600 mb-3 group-hover:text-gray-400 transition-colors" size={24} />
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleStudentImagesChange}
                  className="text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="md:col-span-2 w-full py-4 bg-white text-black rounded-2xl font-bold text-lg hover:bg-gray-200 transition-all flex items-center justify-center gap-3 disabled:opacity-50 shadow-[0_0_40px_rgba(255,255,255,0.1)]"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="animate-spin" size={22} />
                  {loadingStatus || "Analyzing..."}
                </span>
              ) : (
                <>
                  <Sparkles size={22} />
                  Start Gap Analysis
                </>
              )}
            </button>
          </form>
        ) : (
          <div className="space-y-12">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button onClick={resetAnalysis} className="p-2 hover:bg-white/10 rounded-full transition-colors group">
                  <ArrowLeft size={20} className="text-gray-500 group-hover:text-white" />
                </button>
                <h2 className="text-3xl font-bold tracking-tight">Analysis Results</h2>
              </div>
              <div className="px-4 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium">
                AI-Generated Report
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => void generateNotes(undefined, true)}
                disabled={generatingId === "all"}
                className="px-6 py-3 bg-white text-black rounded-xl font-bold text-sm hover:bg-gray-200 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
              >
                {generatingId === "all" ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
                GENERATE ALL NOTES
              </button>
            </div>

            <div className="space-y-6">
              <h3 className="text-sm uppercase tracking-widest text-gray-500 font-semibold flex items-center gap-2">
                <FileText size={16} />
                Course Knowledge Map
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.faculty_knowledge_map?.map((item, i) => (
                  <div key={i} className="glass-card p-4 group">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-bold text-white group-hover:text-blue-400 transition-colors">{item.topic}</h4>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                        item.importance === "High"
                          ? "border-red-500/50 text-red-400 bg-red-500/10"
                          : item.importance === "Medium"
                          ? "border-yellow-500/50 text-yellow-400 bg-yellow-500/10"
                          : "border-green-500/50 text-green-400 bg-green-500/10"
                      }`}>
                        {item.importance} Priority
                      </span>
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed mb-2">
                      {typeof item.description === "string"
                        ? item.description
                        : item.description && typeof item.description === "object"
                        ? String((item.description as { description?: string; text?: string }).description || (item.description as { text?: string }).text || "")
                        : ""}
                    </p>
                    <div className="text-[10px] text-gray-600 font-mono">
                      {typeof item.page_reference === "string" ? item.page_reference : ""}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-8">
              <div className="space-y-4">
                <h3 className="text-sm uppercase tracking-widest text-red-500 font-semibold flex items-center gap-2">
                  <AlertCircle size={16} />
                  Missing Topics
                </h3>

                <div className="grid gap-4">
                  {results.missing_topics?.map((item, i) => (
                    <div key={i} className="glass-card p-6 group">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4">
                          <div className="p-2 rounded-lg bg-red-500/10 text-red-500 group-hover:bg-red-500 group-hover:text-white transition-all duration-300">
                            <AlertCircle size={20} />
                          </div>
                          <div>
                            <h3 className="font-bold text-lg text-white mb-1 group-hover:text-red-400 transition-colors">{item.topic}</h3>
                            <p className="text-gray-400 text-sm leading-relaxed">{item.summary}</p>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => void generateNotes(item)}
                          disabled={generatingId === item.topic}
                          className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-bold text-blue-400 transition-all flex items-center gap-2 whitespace-nowrap disabled:opacity-50"
                        >
                          {generatingId === item.topic && <Loader2 className="animate-spin" size={12} />}
                          GENERATE NOTES
                          <Sparkles size={12} />
                        </button>
                      </div>
                    </div>
                  ))}

                  {results.missing_topics?.length === 0 && (
                    <p className="text-gray-600 text-sm italic">No critical gaps found!</p>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm uppercase tracking-widest text-yellow-500 font-semibold flex items-center gap-2">
                  <HelpCircle size={16} />
                  Partially Covered
                </h3>

                <div className="grid gap-4">
                  {results.partially_covered_topics?.map((item, i) => (
                    <div key={i} className="glass-card p-6 group">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4">
                          <div className="p-2 rounded-lg bg-yellow-500/10 text-yellow-500 group-hover:bg-yellow-500 group-hover:text-white transition-all duration-300">
                            <HelpCircle size={20} />
                          </div>
                          <div>
                            <h3 className="font-bold text-lg text-white mb-1 group-hover:text-yellow-400 transition-colors">{item.topic}</h3>
                            <p className="text-gray-400 text-sm leading-relaxed">{item.summary}</p>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => void generateNotes(item)}
                          disabled={generatingId === item.topic}
                          className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-bold text-blue-400 transition-all flex items-center gap-2 whitespace-nowrap disabled:opacity-50"
                        >
                          {generatingId === item.topic && <Loader2 className="animate-spin" size={12} />}
                          COMPLETE NOTES
                          <Sparkles size={12} />
                        </button>
                      </div>
                    </div>
                  ))}

                  {results.partially_covered_topics?.length === 0 && (
                    <p className="text-gray-600 text-sm italic">All mentioned topics are complete.</p>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm uppercase tracking-widest text-green-500 font-semibold flex items-center gap-2">
                  <CheckCircle2 size={16} />
                  Mastered Topics
                </h3>

                <div className="flex flex-wrap gap-3">
                  {results.covered_topics?.map((topic, i) => (
                    <div key={i} className="px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm hover:bg-green-500/20 transition-colors">
                      {topic}
                    </div>
                  ))}

                  {results.covered_topics?.length === 0 && (
                    <p className="text-gray-600 text-sm italic">No topics fully covered yet.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-20 glass-card p-6">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Sparkles className="text-blue-500" size={20} />
                Ask about these gaps
              </h3>

              <div className="space-y-4 mb-6 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10">
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white rounded-tr-none"
                        : "bg-white/10 text-gray-200 rounded-tl-none"
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
              </div>

              <form onSubmit={handleChat} className="relative">
                <input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="How can I study the missing topics better?"
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-4 pr-12 text-sm focus:outline-none focus:border-blue-500 transition-all"
                />
                <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors">
                  <Send size={16} />
                </button>
              </form>
            </div>
          </div>
        )}

        <AnimatePresence>
          {activeNotes && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-black/85 backdrop-blur-xl"
            >
              <motion.div
                initial={{ y: 20 }}
                animate={{ y: 0 }}
                className="w-full max-w-5xl max-h-[92vh] overflow-hidden flex flex-col relative rounded-3xl border border-white/10 bg-[#090909] shadow-[0_30px_100px_rgba(0,0,0,0.7)]"
              >
                <div className="p-6 md:px-8 border-b border-white/10 flex justify-between items-center bg-white/[0.025] backdrop-blur-xl">
                  <div className="flex items-center gap-3">
                    <BookOpen className="text-blue-500" size={20} />
                    <div>
                      <div className="text-[10px] uppercase tracking-[0.25em] text-blue-400 font-bold mb-1">AI Study Guide</div>
                      <h3 className="text-xl md:text-2xl font-bold tracking-tight">{activeNotes.topic}</h3>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="relative group">
                      <button type="button" className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold flex items-center gap-2 transition-all">
                        <Download size={16} />
                        Download
                      </button>
                      <div className="absolute right-0 top-full pt-2 hidden group-hover:block group-focus-within:block z-20">
                        <div className="w-36 rounded-xl border border-white/10 bg-[#111] p-1 shadow-2xl">
                          <button
                            type="button"
                            onClick={() => downloadNotesTxt(activeNotes)}
                            className="w-full rounded-lg px-3 py-2 text-left text-sm text-gray-200 hover:bg-white/10 transition-colors"
                          >
                            Download .txt
                          </button>
                          <button
                            type="button"
                            onClick={() => void downloadNotesPdf(activeNotes)}
                            className="w-full rounded-lg px-3 py-2 text-left text-sm text-gray-200 hover:bg-white/10 transition-colors"
                          >
                            Download .pdf
                          </button>
                        </div>
                      </div>
                    </div>
                    <button onClick={() => setActiveNotes(null)} className="p-2.5 hover:bg-white/10 rounded-xl transition-colors" aria-label="Close study guide">
                      <X size={20} />
                    </button>
                  </div>
                </div>

                <div className="p-6 md:p-10 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10">
                  {Array.isArray(activeNotes.content) ? (
                    <div className="space-y-12">
                      {activeNotes.content.map((note, idx) => (
                        <div key={idx} className="space-y-6 pb-8 border-b border-white/5 last:border-0">
                          <div>
                            <div className="text-[10px] uppercase tracking-[0.2em] text-gray-500 font-bold mb-2">Topic {idx + 1}</div>
                            <h4 className="text-2xl md:text-3xl font-bold tracking-tight text-white">{note.topic || "Study Topic"}</h4>
                          </div>

                          {note.why_needed && (
                            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                              <h6 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-1">Why this is needed</h6>
                              {renderNoteText(note.why_needed)}
                            </div>
                          )}

                          {note.student_knowledge && (
                            <div className="p-4 bg-white/[0.025] border border-white/10 rounded-xl">
                              <h6 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">What you already know</h6>
                              {renderNoteText(note.student_knowledge)}
                            </div>
                          )}

                          {note.missing_information?.length ? (
                            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                              <h6 className="text-xs font-bold text-red-400 uppercase tracking-widest mb-2">Missing Information</h6>
                              <ul className="text-sm text-gray-300 space-y-1 list-disc pl-4">
                                {note.missing_information.map((item, index) => <li key={index}>{item}</li>)}
                              </ul>
                            </div>
                          ) : null}

                          <div className="grid gap-6">
                            {note.sections?.map((s, sidx) => (
                              <div key={sidx} className="space-y-2">
                                <h5 className="font-bold text-white text-md">{s.heading}</h5>
                                {renderNoteText(s.content)}

                                {s.equations?.map((eq, eqidx) => (
                                  <div key={eqidx}>{<KatexEquation value={eq} />}</div>
                                ))}
                              </div>
                            ))}
                          </div>

                          <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
                            <h6 className="text-xs font-bold text-yellow-500 uppercase tracking-widest mb-2">Exam Points</h6>
                            <ul className="text-sm text-gray-300 space-y-1 list-disc pl-4">
                              {note.exam_points?.map((p, pidx) => <li key={pidx}>{p}</li>)}
                            </ul>
                          </div>

                          {note.sources?.length ? (
                            <div className="text-xs text-gray-600 font-mono text-right">
                              Sources: {note.sources.join(", ")}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-8">
                      {activeNotes.content.why_needed && (
                        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                          <h6 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-1">Why this is needed</h6>
                          {renderNoteText(activeNotes.content.why_needed)}
                        </div>
                      )}

                      {activeNotes.content.missing_information?.length ? (
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                          <h6 className="text-xs font-bold text-red-400 uppercase tracking-widest mb-2">Missing Information</h6>
                          <ul className="text-sm text-gray-300 space-y-1 list-disc pl-4">
                            {activeNotes.content.missing_information.map((item, index) => <li key={index}>{item}</li>)}
                          </ul>
                        </div>
                      ) : null}

                      <div className="grid gap-8">
                        {activeNotes.content.sections?.map((s, sidx) => (
                          <div key={sidx} className="space-y-3">
                            <h4 className="text-lg font-bold text-white">{s.heading}</h4>
                            {renderNoteText(s.content)}

                            {s.equations?.map((eq, eqidx) => (
                              <div key={eqidx}>{<KatexEquation value={eq} />}</div>
                            ))}
                          </div>
                        ))}
                      </div>

                      <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
                        <h6 className="text-xs font-bold text-yellow-500 uppercase tracking-widest mb-2">Exam Points</h6>
                        <ul className="text-sm text-gray-300 space-y-1 list-disc pl-4">
                          {activeNotes.content.exam_points?.map((p, pidx) => <li key={pidx}>{p}</li>)}
                        </ul>
                      </div>

                      {activeNotes.content.sources?.length ? (
                        <div className="text-xs text-gray-600 font-mono text-right">
                          Sources: {activeNotes.content.sources.join(", ")}
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}