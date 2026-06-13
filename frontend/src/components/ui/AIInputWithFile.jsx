import { CornerRightUp, FileUp, Paperclip, X } from 'lucide-react'
import { useState } from 'react'
import { useFileInput } from '../hooks/useFileInput'
import { useAutoResizeTextarea } from '../hooks/useAutoResizeTextarea'

function FileDisplay({ fileName, onClear }) {
  return (
    <div className="ai-input-file">
      <FileUp className="ai-input-file-icon" />
      <span className="ai-input-file-name">{fileName}</span>
      <button type="button" onClick={onClear} className="ai-input-file-clear" aria-label="Remove file">
        <X className="ai-input-file-clear-icon" />
      </button>
    </div>
  )
}

/**
 * Auto-resizing chat input with an optional file attachment.
 *
 * Props:
 *  - onSubmit(message, file?) — called on Enter (without Shift) or send click
 *  - placeholder, minHeight, maxHeight, accept, maxFileSize, disabled, className
 */
export function AIInputWithFile({
  id = 'ai-input-with-file',
  placeholder = 'Type a question…',
  minHeight = 52,
  maxHeight = 200,
  accept = 'image/*',
  maxFileSize = 5,
  disabled = false,
  onSubmit,
  className = '',
}) {
  const [inputValue, setInputValue] = useState('')
  const { fileName, fileInputRef, handleFileSelect, clearFile, selectedFile } = useFileInput({
    accept,
    maxSize: maxFileSize,
  })

  const { textareaRef, adjustHeight } = useAutoResizeTextarea({ minHeight, maxHeight })

  const hasContent = inputValue.trim() || selectedFile

  const handleSubmit = () => {
    if (disabled || !hasContent) return
    onSubmit?.(inputValue, selectedFile ?? undefined)
    setInputValue('')
    clearFile()
    adjustHeight(true)
  }

  return (
    <div className={`ai-input ${className}`.trim()}>
      <div className="ai-input-inner">
        {fileName && <FileDisplay fileName={fileName} onClear={clearFile} />}

        <div className="ai-input-field">
          <div
            className="ai-input-attach"
            role="button"
            tabIndex={0}
            aria-label="Attach file"
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                fileInputRef.current?.click()
              }
            }}
          >
            <Paperclip className="ai-input-attach-icon" />
          </div>

          <input
            type="file"
            className="ai-input-file-hidden"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept={accept}
          />

          <textarea
            id={id}
            className="ai-input-textarea"
            placeholder={placeholder}
            ref={textareaRef}
            value={inputValue}
            disabled={disabled}
            rows={1}
            onChange={(e) => {
              setInputValue(e.target.value)
              adjustHeight()
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
          />

          <button
            type="button"
            className="ai-input-send"
            onClick={handleSubmit}
            disabled={disabled || !hasContent}
            aria-label="Send"
          >
            <CornerRightUp className={`ai-input-send-icon ${hasContent ? 'is-active' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  )
}
