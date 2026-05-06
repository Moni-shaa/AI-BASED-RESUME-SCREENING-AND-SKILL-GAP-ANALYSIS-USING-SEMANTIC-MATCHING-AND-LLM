import React, { useState, useEffect } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  MapPin,
  Star,
  Send,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  MessageSquare,
  Bot,
  HelpCircle,
  FileText,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { apiService } from "../services/api";
import toast from "react-hot-toast";
import config from "../config";
import SmartRecommendations from "./SmartRecommendations";

const CandidateDetail = () => {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(
    searchParams.get("tab") || "overview",
  );
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [interviewQuestions, setInterviewQuestions] = useState(null);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  
  useEffect(() => {
    console.log("Candidate Data:", candidate);
  }, [candidate]);
  // Format AI responses for better display
  const formatAIResponse = (text) => {
    return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") // Bold text
    .replace(/\*(.*?)\*/g, "<em>$1</em>") // Italic text
    .replace(/(\d+\.\s)/g, "<br/><strong>$1</strong>") // Numbered lists
    .replace(/(-\s)/g, "<br/>• ") // Bullet points
    .replace(/\n/g, "<br/>") // Line breaks
    .replace(/^<br\/>/, ""); // Remove leading break
  };
  
  useEffect(() => {
    fetchCandidateData();
  }, [id]);
  
  useEffect(() => {
    setSearchParams({ tab: activeTab });
  }, [activeTab, setSearchParams]);
  
  const fetchCandidateData = async () => {
    try {
      const [candidateResponse, biasResponse] = await Promise.all([
        apiService.getCandidate(id),
        // Don't fail if bias analysis is not available
      ]);
      
      const data = candidateResponse.data;
      
      setCandidate({
        ...data.candidate,
        
        matched_skills: data.matched_skills,
        missing_skills: data.missing_skills,
        resume_skills: data.resume_skills,
        jd_skills: data.jd_skills,
        
        priority_map: data.candidate.priority_map,
        score_breakdown: data.candidate.score_breakdown,
        match_score: data.candidate.match_score,
        semantic_score: data.candidate.semantic_score, 
        final_score: data.candidate.final_score,
        
        shortlisted: data.candidate.shortlisted,
        decision_reason: data.candidate.decision_reason,
      });
      
      // Fetch blind resume if bias analysis exists
    } catch (error) {
      console.error("Error fetching candidate data:", error);
      toast.error("Failed to load candidate data");
    } finally {
      setLoading(false);
    }
  };
  
  const handleSendMessage = async () => {
    if (!newMessage.trim() || isChatLoading) return;
    
    const userMessage = newMessage.trim();
    setNewMessage("");
    setIsChatLoading(true);
    
    // Add user message to chat
    const newUserMessage = {
      type: "user",
      message: userMessage,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, newUserMessage]);
    
    try {
      const response = await apiService.chatWithCandidate(id, userMessage);
      
      // Add AI response to chat
      const aiMessage = {
        type: "ai",
        message: response.data.reply,
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Failed to send message");
      
      // Add error message
      const errorMessage = {
        type: "ai",
        message: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };
  
  const getCategoryIcon = (category) => {
    switch (category) {
      case "Highly Qualified":
      return <CheckCircle className="h-5 w-5 text-success-500" />;
      case "Qualified":
      return <AlertTriangle className="h-5 w-5 text-warning-500" />;
      case "Not a Fit":
      return <XCircle className="h-5 w-5 text-danger-500" />;
      default:
      return <User className="h-5 w-5 text-gray-500" />;
    }
  };
  
  const getCategoryColor = (category) => {
    switch (category) {
      case "Highly Qualified":
      return "badge-success";
      case "Qualified":
      return "badge-warning";
      case "Not a Fit":
      return "badge-danger";
      default:
      return "badge-primary";
    }
  };
  const priorityData = candidate
    ? [
        {
          name: "High",
          value: candidate.priority_map?.high_priority?.length || 0,
        },
        {
          name: "Medium",
          value: candidate.priority_map?.medium_priority?.length || 0,
        },
        {
          name: "Low",
          value: candidate.priority_map?.low_priority?.length || 0,
        },
        {
          name: "Missing",
          value: candidate.missing_skills?.length || 0,
        },
      ].filter((item) => item.value > 0)
    : [];
  const contributionData = candidate?.score_breakdown
  ? [
    {
      name: "Matched",
      value: candidate.score_breakdown.matched?.length || 0,
    },
    {
      name: "Missing High",
      value: candidate.score_breakdown.missing_high?.length || 0,
    },
    {
      name: "Missing Medium",
      value: candidate.score_breakdown.missing_medium?.length || 0,
    },
  ]
  : [];
  
  const tabs = [
    { id: "overview", label: "Overview", icon: User },
    { id: "analysis", label: "AI Analysis", icon: TrendingUp },
    { id: "interview", label: "Interview Guide", icon: HelpCircle },
    { id: "smarttips", label: "Smart Tips", icon: Bot },
  ];
  
  if (loading) {
    return (
      <div className="space-y-6">
      <div className="flex items-center space-x-4">
      <div className="h-8 w-8 bg-gray-200 rounded animate-pulse"></div>
      <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
      </div>
      <div className="card p-6">
      <div className="animate-pulse space-y-4">
      <div className="h-6 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      </div>
      </div>
      </div>
    );
  }
  
  if (!candidate) {
    return (
      <div className="text-center py-12">
      <User className="h-16 w-16 text-gray-400 mx-auto mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
      Candidate not found
      </h2>
      <p className="text-gray-600 mb-6">
      The candidate you're looking for doesn't exist.
      </p>
      <Link to="/candidates" className="btn-primary">
      <ArrowLeft className="h-4 w-4 mr-2" />
      Back to Candidates
      </Link>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center space-x-4">
          <Link
            to="/candidates"
            className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {candidate.analysis?.contact_info?.name || candidate.filename}
            </h1>
            <p className="text-gray-600">
              Uploaded {new Date(candidate.upload_date).toLocaleDateString()}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span
            className={`badge ${
              candidate.shortlisted ? "badge-success" : "badge-danger"
            }`}
          >
            {candidate.shortlisted ? (
              <CheckCircle className="h-4 w-4 mr-1" />
            ) : (
              <XCircle className="h-4 w-4 mr-1" />
            )}
            {candidate.shortlisted ? "Shortlisted" : "Rejected"}
          </span>

          <div className="flex items-center space-x-2 text-sm">
            <Star className="h-4 w-4 text-yellow-500" />
            <span className="font-medium">{candidate.final_score ?? 0}%</span>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="border-b border-gray-200"
      >
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeTab === tab.id
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </motion.div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === "overview" && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Contact Info */}
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Contact Information
                  </h3>
                  <div className="space-y-3">
                    {candidate.analysis?.contact_info?.name && (
                      <div className="flex items-center space-x-3">
                        <User className="h-4 w-4 text-gray-400" />
                        <span className="text-gray-900">
                          {candidate.analysis.contact_info.name}
                        </span>
                      </div>
                    )}
                    {candidate.analysis?.contact_info?.email && (
                      <div className="flex items-center space-x-3">
                        <Mail className="h-4 w-4 text-gray-400" />
                        <span className="text-gray-900">
                          {candidate.analysis.contact_info.email}
                        </span>
                      </div>
                    )}
                    {candidate.analysis?.contact_info?.phone && (
                      <div className="flex items-center space-x-3">
                        <Phone className="h-4 w-4 text-gray-400" />
                        <span className="text-gray-900">
                          {candidate.analysis.contact_info.phone}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Skills */}
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Key Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {candidate.analysis?.key_skills?.map((skill, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-primary-50 text-primary-700 text-sm rounded-full"
                      >
                        {skill}
                      </span>
                    )) || <p className="text-gray-500">No skills identified</p>}
                  </div>
                </div>
                <div className="card p-6 lg:col-span-3">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Skill Gap Analysis
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-blue-50 border border-blue-100 rounded-xl p-6 text-center">
                      <p className="text-sm text-gray-500">JD Skills</p>
                      <p className="text-3xl font-bold text-blue-600">
                        {candidate.jd_skills?.length || 0}
                      </p>
                    </div>

                    <div className="bg-green-50 border border-green-100 rounded-xl p-6 text-center">
                      <p className="text-sm text-gray-500">Matched Skills</p>
                      <p className="text-3xl font-bold text-green-600">
                        {candidate.matched_skills?.length || 0}
                      </p>
                    </div>

                    <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-center">
                      <p className="text-sm text-gray-500">Skill Gap</p>
                      <p className="text-3xl font-bold text-red-600">
                        {candidate.missing_skills?.length || 0}
                      </p>
                    </div>
                  </div>
                </div>

                {candidate.resume_skills && candidate.jd_skills && (
                  <div className="card p-6 lg:col-span-3">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <CheckCircle className="h-5 w-5 text-success-500 mr-2" />
                      Matched Skills (Resume vs JD)
                    </h3>

                    <div className="flex flex-wrap gap-2">
                      {candidate.resume_skills
                        .filter((skill) => candidate.jd_skills.includes(skill))
                        .map((skill, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-success-50 text-success-700 text-sm rounded-full"
                          >
                            {skill}
                          </span>
                        ))}
                    </div>
                  </div>
                )}

                {/* ✅ Missing Skills */}
                {candidate.missing_skills?.length > 0 && (
                  <div className="card p-6 lg:col-span-3">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                      <AlertTriangle className="h-5 w-5 text-danger-500 mr-2" />
                      Missing Skills (Skill Gap)
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {candidate.missing_skills.map((skill, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-danger-50 text-danger-700 text-sm rounded-full"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:col-span-3">
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <CheckCircle className="h-5 w-5 text-success-500 mr-2" />
                    Strengths
                  </h3>

                  <ul className="space-y-2">
                    {candidate.analysis?.strengths?.map((strength, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-gray-700"
                      >
                        <CheckCircle className="h-4 w-4 text-green-500 mt-1" />
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <AlertTriangle className="h-5 w-5 text-warning-500 mr-2" />
                    Weaknesses
                  </h3>

                  <ul className="space-y-2">
                    {candidate.analysis?.weaknesses?.map((weakness, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-gray-700"
                      >
                        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-1" />
                        {weakness}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}

          {activeTab === "analysis" && (
            <div className="space-y-6">
              {/* ✅ Weighted Match Score */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Resume Matching Scores
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                  <div className="bg-primary-50 border rounded-xl p-6">
                    <p className="text-sm text-gray-500">Skill Match Score</p>
                    <p className="text-3xl font-bold text-primary-600">
                      {candidate.match_score ?? 0}%
                    </p>
                  </div>

                  <div className="bg-blue-50 border rounded-xl p-6">
                    <p className="text-sm text-gray-500">Semantic Similarity</p>
                    <p className="text-3xl font-bold text-blue-600">
                      {candidate.semantic_score
                        ? candidate.semantic_score.toFixed(2)
                        : 0}
                      %
                    </p>
                  </div>

                  <div
                    className={`border rounded-xl p-6 ${
                      candidate.shortlisted ? "bg-green-50" : "bg-red-50"
                    }`}
                  >
                    <p className="text-sm text-gray-500">Decision</p>
                    <p className="text-xl font-bold">
                      {candidate.shortlisted ? "Shortlisted" : "Rejected"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-4">
                  Recruiter Priority Distribution
                </h3>

                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={priorityData}
                      dataKey="value"
                      nameKey="name"
                      outerRadius={100}
                      label
                    >
                      <Cell fill="#ef4444" /> {/* High */}
                      <Cell fill="#facc15" /> {/* Medium */}
                      <Cell fill="#3b82f6" /> {/* Low */}
                      <Cell fill="#6b7280" /> {/* Missing */}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              {/* ✅ Priority Breakdown */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Recruiter Priority Breakdown
                </h3>

                {candidate.score_breakdown ? (
                  <div className="space-y-4">
                    {/* Matched */}
                    <div>
                      <p className="text-sm font-medium text-success-700 mb-2">
                        Matched Skills
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {candidate.score_breakdown.matched?.map((skill, i) => (
                          <span
                            key={i}
                            className="px-3 py-1 bg-success-50 text-success-700 text-sm rounded-full"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Missing High */}
                    {candidate.score_breakdown.missing_high?.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-danger-700 mb-2">
                          Missing High Priority Skills
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {candidate.score_breakdown.missing_high.map(
                            (skill, i) => (
                              <span
                                key={i}
                                className="px-3 py-1 bg-danger-50 text-danger-700 text-sm rounded-full"
                              >
                                {skill}
                              </span>
                            ),
                          )}
                        </div>
                      </div>
                    )}

                    {/* Missing Medium */}
                    {candidate.score_breakdown.missing_medium?.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-warning-700 mb-2">
                          Missing Medium Priority Skills
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {candidate.score_breakdown.missing_medium.map(
                            (skill, i) => (
                              <span
                                key={i}
                                className="px-3 py-1 bg-warning-50 text-warning-700 text-sm rounded-full"
                              >
                                {skill}
                              </span>
                            ),
                          )}
                        </div>
                      </div>
                    )}
                    {/* AI Hiring Insight */}
                    <div className="mt-6 p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
                      <h4 className="text-md font-semibold text-blue-900 mb-4 flex items-center gap-2">
                        🧠 AI Hiring Insight
                      </h4>

                      {/* Score Summary */}
                      <div className="mb-4">
                        <p className="text-sm font-semibold text-gray-700 mb-2">
                          📊 Score Summary
                        </p>

                        <div className="flex flex-wrap gap-4 text-sm">
                          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
                            Match: {candidate.match_score}%
                          </span>

                          <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full">
                            Semantic: {candidate.semantic_score?.toFixed(2)}%
                          </span>

                          <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full">
                            Final: {candidate.final_score}%
                          </span>
                        </div>
                      </div>
                      <hr className="my-5 border-gray-200" />

                      {/* AI Reasoning */}
                      <div className="pt-4 border-t border-blue-200">
                        <p className="text-sm font-semibold text-gray-700 mb-2"></p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-700">
                          {/* Strengths */}
                          <div>
                            <span className="font-semibold text-green-600">
                              ✅ Strengths
                            </span>
                            <ul className="list-disc ml-5 mt-2">
                              {candidate.score_breakdown?.matched
                                ?.slice(0, 4)
                                .map((skill, i) => (
                                  <li key={i}>{skill}</li>
                                ))}
                            </ul>
                          </div>

                          {/* Missing Skills */}
                          {candidate.score_breakdown?.missing_high?.length >
                            0 && (
                            <div>
                              <span className="font-semibold text-red-600">
                                ⚠ Missing Critical Skills
                              </span>
                              <ul className="list-disc ml-5 mt-2">
                                {candidate.score_breakdown.missing_high.map(
                                  (skill, i) => (
                                    <li key={i}>{skill}</li>
                                  ),
                                )}
                              </ul>
                            </div>
                          )}

                          {/* Hiring Decision */}
                          <div className="md:col-span-2">
                            <span className="font-semibold text-blue-700">
                              🎯 Hiring Decision
                            </span>
                            <p className="mt-2">
                              {candidate.shortlisted
                                ? `Even though some critical skills like ${
                                    candidate.score_breakdown?.missing_high?.join(
                                      ", ",
                                    ) || "none"
                                  } are missing, the candidate demonstrates strong alignment with other key technologies and meets the shortlist threshold.`
                                : `The candidate does not meet the shortlist threshold because important high-priority skills such as ${
                                    candidate.score_breakdown?.missing_high?.join(
                                      ", ",
                                    ) || "multiple skills"
                                  } are missing.`}
                            </p>
                          </div>
                          <div>
                      <span className="font-semibold">💡 Recommendation</span>
                      <ul className="list-disc ml-5 mt-1">
                        {candidate.score_breakdown?.missing_high?.length > 0 ? (
                          <li>
                            Improve expertise in{" "}
                            {candidate.score_breakdown.missing_high.join(", ")}.
                          </li>
                        ) : (
                          <li>
                            Strengthen advanced technical and cloud deployment
                            skills.
                          </li>
                        )}
                        <li>
                          Continue developing expertise in the matched
                          technologies.
                        </li>
                      </ul>
                    </div>
                        </div>
                      </div>
                    </div>
                    
                  </div>
                ) : (
                  <p className="text-gray-500">No breakdown available</p>
                )}
              </div>

              <div className="card p-6 mt-6">
                <h3 className="text-lg font-semibold mb-4">
                  Skill Contribution to Score
                </h3>

                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={contributionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#6366f1" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {activeTab === "interview" && (
            <InterviewQuestionsTab
              candidateId={id}
              interviewQuestions={interviewQuestions}
              setInterviewQuestions={setInterviewQuestions}
            />
          )}
          {activeTab === "smarttips" && (
            <SmartRecommendations candidateId={id} />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
  };
  
  // Sub-component for Interview Questions to keep main component clean
  const InterviewQuestionsTab = ({
    candidateId,
    interviewQuestions,
    setInterviewQuestions,
  }) => {
    const [loading, setLoading] = useState(!interviewQuestions);
    const [error, setError] = useState(null);
    
    useEffect(() => {
      if (!interviewQuestions) {
        loadQuestions();
      }
    }, []);
    
    const loadQuestions = async () => {
      setLoading(true);
      try {
        const response = await apiService.getInterviewQuestions(candidateId);
        setInterviewQuestions(response.data);
      } catch (err) {
        console.error("Error loading interview questions:", err);
        setError("Failed to load interview questions. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    
    if (loading) {
      return (
        <div className="card p-12 text-center space-y-4">
        <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="mx-auto w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full"
        />
        <p className="text-gray-600">
        Generating tailored interview questions...
        </p>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="card p-8 text-center">
        <AlertTriangle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
        Error Loading Questions
        </h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={loadQuestions} className="btn-primary">
        Try Again
        </button>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
      <HelpCircle className="h-5 w-5 text-blue-500 mt-0.5" />
      <div>
      <h4 className="font-semibold text-blue-900">
      AI-Generated Interview Guide
      </h4>
      <p className="text-sm text-blue-700">
      These questions are tailored specifically to this candidate's
      profile, focusing on validating their strengths and probing their
      weaknesses.
      </p>
      </div>
      </div>
      
      {interviewQuestions?.technical_questions?.length > 0 && (
        <div className="card overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
        <FileText className="h-5 w-5 text-gray-500 mr-2" />
        Technical Verification
        </h3>
        </div>
        <div className="divide-y divide-gray-200">
        {interviewQuestions.technical_questions.map((q, i) => (
          <div key={i} className="p-6 hover:bg-gray-50 transition-colors">
          <p className="font-medium text-gray-900 mb-2">
          Q{i + 1}: {q.question}
          </p>
          <div className="flex items-start space-x-2 text-sm text-gray-600 bg-gray-50 p-3 rounded">
          <span className="font-semibold text-gray-500 uppercase text-xs tracking-wider mt-0.5">
          Expected:
          </span>
          <span>{q.expected_answer_points}</span>
          </div>
          </div>
        ))}
        </div>
        </div>
      )}
      
      {interviewQuestions?.behavioral_questions?.length > 0 && (
        <div className="card overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
        <User className="h-5 w-5 text-gray-500 mr-2" />
        Behavioral & Cultural Fit
        </h3>
        </div>
        <div className="divide-y divide-gray-200">
        {interviewQuestions.behavioral_questions.map((q, i) => (
          <div key={i} className="p-6 hover:bg-gray-50 transition-colors">
          <p className="font-medium text-gray-900 mb-2">
          Q{i + 1}: {q.question}
          </p>
          <div className="flex items-start space-x-2 text-sm text-gray-600 bg-gray-50 p-3 rounded">
          <span className="font-semibold text-gray-500 uppercase text-xs tracking-wider mt-0.5">
          Looking For:
          </span>
          <span>{q.looking_for}</span>
          </div>
          </div>
        ))}
        </div>
        </div>
      )}
      
      {interviewQuestions?.soft_skills_questions?.length > 0 && (
        <div className="card overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
        <MessageSquare className="h-5 w-5 text-gray-500 mr-2" />
        Soft Skills Assessment
        </h3>
        </div>
        <div className="divide-y divide-gray-200">
        {interviewQuestions.soft_skills_questions.map((q, i) => (
          <div key={i} className="p-6 hover:bg-gray-50 transition-colors">
          <p className="font-medium text-gray-900 mb-2">
          Q{i + 1}: {q.question}
          </p>
          <div className="flex items-start space-x-2 text-sm text-gray-600 bg-gray-50 p-3 rounded">
          <span className="font-semibold text-gray-500 uppercase text-xs tracking-wider mt-0.5">
          Purpose:
          </span>
          <span>{q.purpose}</span>
          </div>
          </div>
        ))}
        </div>
        </div>
      )}
      </div>
    );
  };
  
  export default CandidateDetail;
  