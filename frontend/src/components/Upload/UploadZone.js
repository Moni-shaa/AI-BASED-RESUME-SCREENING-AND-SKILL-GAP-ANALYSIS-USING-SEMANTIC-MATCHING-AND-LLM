import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import toast from "react-hot-toast";
import config from "../../config";
import { apiService } from "../../services/api";

const UploadZone = ({ onUploadSuccess, onUploadStart }) => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [jdFile, setJdFile] = useState(null); // ✅ NEW STATE
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.file.size > config.MAX_FILE_SIZE) {
        toast.error("File size too large. Maximum size is 16MB.");
      } else {
        toast.error("Invalid file type. Only PDF and DOCX files are allowed.");
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setUploadedFile(file);
      toast.success("File selected successfully!");
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      accept: {
        "application/pdf": [".pdf"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
          [".docx"],
      },
      maxSize: config.MAX_FILE_SIZE,
      multiple: false,
    });

  const removeFile = () => {
    setUploadedFile(null);
    setUploadProgress(0);
  };

  // ✅ NEW HANDLER
  const handleJdFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setJdFile(file);
      toast.success("Job Description file selected!");
    }
  };

  const handleUpload = async () => {
    if (!uploadedFile) {
      toast.error("Please select a file first.");
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    onUploadStart?.();

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + Math.random() * 20;
      });
    }, 200);

    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      // ✅ Only append if exists
      if (jobDescription.trim()) {
        formData.append("job_description", jobDescription);
      }

      if (jdFile) {
        formData.append("jd_file", jdFile);
      }

      const response = await apiService.uploadResume(formData);

      clearInterval(progressInterval);
      setUploadProgress(100);

      setTimeout(() => {
        toast.success("Resume analyzed successfully!");
        onUploadSuccess?.(response.data);

        // Reset form
        setUploadedFile(null);
        setJobDescription("");
        setJdFile(null); // ✅ RESET JD FILE
        setUploadProgress(0);
      }, 500);
    } catch (error) {
      clearInterval(progressInterval);
      console.error("Upload error:", error);
      toast.error(
        error.response?.data?.error ||
          "Failed to upload resume. Please try again.",
      );
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <motion.div
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
          isDragActive
            ? "border-primary-400 bg-gradient-to-br from-primary-50 to-primary-100 shadow-lg"
            : "border-gray-300 hover:border-primary-300 hover:bg-gradient-to-br hover:from-gray-50 hover:to-gray-100 hover:shadow-md"
        }`}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        {...getRootProps()}
      >
        <input {...getInputProps()} />

        <div className="space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full flex items-center justify-center bg-gray-100">
            {isDragReject ? (
              <AlertCircle className="h-8 w-8 text-danger-500" />
            ) : (
              <Upload className="h-8 w-8 text-gray-500" />
            )}
          </div>

          <div>
            <p className="text-lg font-semibold text-gray-900">
              {isDragActive
                ? "Drop the file here"
                : "Drop your resume here, or click to browse"}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Supports PDF and DOCX files up to 16MB
            </p>
          </div>
        </div>
      </motion.div>

      {/* Selected File */}
      <AnimatePresence>
        {uploadedFile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="card p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="h-5 w-5 text-primary-600" />
                <div>
                  <p className="font-medium">{uploadedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(uploadedFile.size)}
                  </p>
                </div>
              </div>

              <button onClick={removeFile}>
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Job Description */}
      <div className="card p-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Job Description (Optional)
        </label>

        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job description here..."
          rows={6}
          className="input-field resize-none"
        />

        {/* ✅ NEW JD FILE UPLOAD */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Job Description File (Optional)
          </label>

          <input
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleJdFileChange}
            className="block w-full text-sm text-gray-600"
          />

          {jdFile && (
            <p className="text-xs text-success-600 mt-1">
              Selected: {jdFile.name}
            </p>
          )}
        </div>
      </div>

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!uploadedFile || isUploading}
        className="btn-primary w-full py-4 rounded-xl"
      >
        {isUploading ? "Analyzing Resume..." : "Upload & Analyze Resume"}
      </button>
    </div>
  );
};

export default UploadZone;
