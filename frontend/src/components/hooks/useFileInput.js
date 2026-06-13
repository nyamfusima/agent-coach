import { useState, useRef } from 'react'

/**
 * Manages a hidden file <input>: validates the chosen file against an
 * `accept` pattern and `maxSize` (MB), and exposes the selected File plus
 * helpers to display and clear it.
 */
export function useFileInput({ accept, maxSize } = {}) {
  const [fileName, setFileName] = useState('')
  const [error, setError] = useState('')
  const [fileSize, setFileSize] = useState(0)
  const [selectedFile, setSelectedFile] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileSelect = (e) => {
    validateAndSetFile(e.target.files?.[0])
  }

  const validateAndSetFile = (file) => {
    setError('')

    if (!file) return

    if (maxSize && file.size > maxSize * 1024 * 1024) {
      setError(`File size must be less than ${maxSize}MB`)
      return
    }

    if (accept && !file.type.match(accept.replace('/*', '/'))) {
      setError(`File type must be ${accept}`)
      return
    }

    setSelectedFile(file)
    setFileSize(file.size)
    setFileName(file.name)
  }

  const clearFile = () => {
    setFileName('')
    setError('')
    setFileSize(0)
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return {
    fileName,
    error,
    fileSize,
    selectedFile,
    fileInputRef,
    handleFileSelect,
    validateAndSetFile,
    clearFile,
  }
}
