"use client";

import { useState, useEffect, FormEvent, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import KnowledgeOrb from "@/components/KnowledgeOrb";
import { Upload, Sparkles, Image as ImageIcon, FileText, ArrowLeft, CheckCircle2, AlertCircle, HelpCircle, Send, Loader2, BookOpen, X } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
      const savedResults = localStorage.getItem("ss_last_results");
      const savedChat = localStorage.getItem("ss_last_chat");
      const savedRaw = localStorage.getItem("ss_faculty_raw");

      if (savedResults && savedResults !== "undefined") setResults(JSON.parse(savedResults));
      if (savedChat && savedChat !== "undefined") setChatHistory(JSON.parse(savedChat));
      if (savedRaw && savedRaw !== "undefined") setFacultyRaw(JSON.parse(savedRaw));
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

    setGeneratingId(id);

    try {
      let currentFacultyData = facultyRaw;

      if (!currentFacultyData) {
        const savedRaw = localStorage.getItem("ss_faculty_raw");
        if (savedRaw && savedRaw !== "undefined") currentFacultyData = JSON.parse(savedRaw);
      }

      const missingTopics = results?.missing_topics || [];
      const partialTopics = results?.partially_covered_topics || [];
      const allTopics = [...missingTopics, ...partialTopics];

      let body;

      if (isAll) {
        body = {
          topic: "All Missing and Partially Covered Topics",
          status: "missing",
          why_needed: "These topics were identified by the gap analysis as missing or only partially covered in the student's notes.",
          student_knowledge: allTopics.map((item) => `${item.topic}: ${item.student_knowledge || "Not sufficiently covered"}`).join("\n"),
          missing_information: allTopics.flatMap((item) => item.missing_information || [item.summary || ""]),
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
                onClick={() => generateNotes(undefined, true)}
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
                    <p className="text-gray-400 text-xs leading-relaxed mb-2">{item.description}</p>
                    <div className="text-[10px] text-gray-600 font-mono">{item.page_reference || ""}</div>
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
                          onClick={() => generateNotes(item)}
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
                          onClick={() => generateNotes(item)}
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
              className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-md"
            >
              <motion.div
                initial={{ y: 20 }}
                animate={{ y: 0 }}
                className="glass-card w-full max-w-3xl max-h-[80vh] overflow-hidden flex flex-col relative"
              >
                <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/[0.02]">
                  <div className="flex items-center gap-3">
                    <BookOpen className="text-blue-500" size={20} />
                    <h3 className="text-xl font-bold">{activeNotes.topic}</h3>
                  </div>

                  <button onClick={() => setActiveNotes(null)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                    <X size={20} />
                  </button>
                </div>

                <div className="p-8 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10">
                  {Array.isArray(activeNotes.content) ? (
                    <div className="space-y-12">
                      {activeNotes.content.map((note, idx) => (
                        <div key={idx} className="space-y-6 pb-8 border-b border-white/5 last:border-0">
                          <h4 className="text-2xl font-bold text-blue-400">{note.topic || "Study Topic"}</h4>

                          {note.why_needed && (
                            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                              <h6 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-1">Why this is needed</h6>
                              <p className="text-sm text-gray-300">{note.why_needed}</p>
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
                                <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-wrap">{s.content}</p>

                                {s.equations?.map((eq, eqidx) => (
                                  <div key={eqidx} className="bg-black/40 p-3 rounded-lg font-mono text-blue-300 text-center my-2 border border-blue-500/20">
                                    {eq}
                                  </div>
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
                          <p className="text-sm text-gray-300">{activeNotes.content.why_needed}</p>
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
                            <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-wrap">{s.content}</p>

                            {s.equations?.map((eq, eqidx) => (
                              <div key={eqidx} className="bg-black/40 p-3 rounded-lg font-mono text-blue-300 text-center my-2 border border-blue-500/20">
                                {eq}
                              </div>
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