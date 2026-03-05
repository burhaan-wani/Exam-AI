import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { syllabusAPI, questionsAPI } from '@/api/client'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { Trash2, Plus } from 'lucide-react'

const BLOOM_LEVELS = [
  { value: 'Remember', label: 'Remember - Recall facts and basic concepts' },
  { value: 'Understand', label: 'Understand - Explain ideas in own words' },
  { value: 'Apply', label: 'Apply - Use information in new situations' },
  { value: 'Analyze', label: 'Analyze - Draw connections and break into parts' },
  { value: 'Evaluate', label: 'Evaluate - Make judgments and justify decisions' },
  { value: 'Create', label: 'Create - Produce new or original work' },
]

const BloomConfig = () => {
  const { syllabusId } = useParams()
  const navigate = useNavigate()
  const [syllabus, setSyllabus] = useState(null)
  const [configs, setConfigs] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [examConfig, setExamConfig] = useState({
    exam_title: 'Examination',
    total_marks: 100,
    duration_minutes: 180,
  })

  useEffect(() => {
    loadSyllabus()
  }, [syllabusId])

  const loadSyllabus = async () => {
    try {
      const response = await syllabusAPI.get(syllabusId)
      setSyllabus(response.data)

      // Initialize configs with first topic
      if (response.data.topics && response.data.topics.length > 0) {
        setConfigs(
          response.data.topics.slice(0, 5).map((topic) => ({
            topic: topic.name,
            bloom_level: 'Remember',
            num_questions: 2,
            marks_per_question: 5,
            difficulty: 'medium',
          }))
        )
      }
    } catch (error) {
      toast.error('Failed to load syllabus')
    } finally {
      setLoading(false)
    }
  }

  const handleAddConfig = () => {
    setConfigs([
      ...configs,
      {
        topic: '',
        bloom_level: 'Remember',
        num_questions: 2,
        marks_per_question: 5,
        difficulty: 'medium',
      },
    ])
  }

  const handleRemoveConfig = (idx) => {
    setConfigs(configs.filter((_, i) => i !== idx))
  }

  const handleConfigChange = (idx, field, value) => {
    const updated = [...configs]
    updated[idx] = { ...updated[idx], [field]: value }
    setConfigs(updated)
  }

  const handleExamConfigChange = (field, value) => {
    setExamConfig((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async () => {
    if (configs.length === 0) {
      toast.error('Add at least one Bloom configuration')
      return
    }

    if (configs.some((c) => !c.topic)) {
      toast.error('All topics must be specified')
      return
    }

    setSubmitting(true)
    try {
      const response = await questionsAPI.createBlueprint({
        syllabus_id: syllabusId,
        ...examConfig,
        configs,
      })

      toast.success('Blueprint created successfully!')
      navigate(`/generate-questions/${response.data.id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create blueprint')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="text-center text-gray-500 py-8">Loading...</div>
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Configure Bloom Levels</h1>
        <p className="text-gray-600">
          Define which Bloom's Taxonomy level to use for each topic
        </p>
      </div>

      {/* Exam Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Exam Configuration</CardTitle>
          <CardDescription>General exam settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Exam Title</label>
            <Input
              value={examConfig.exam_title}
              onChange={(e) => handleExamConfigChange('exam_title', e.target.value)}
              placeholder="e.g., Final Examination"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Total Marks</label>
              <Input
                type="number"
                value={examConfig.total_marks}
                onChange={(e) => handleExamConfigChange('total_marks', parseInt(e.target.value))}
                min="1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Duration (minutes)</label>
              <Input
                type="number"
                value={examConfig.duration_minutes}
                onChange={(e) => handleExamConfigChange('duration_minutes', parseInt(e.target.value))}
                min="1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bloom Configurations */}
      <Card>
        <CardHeader>
          <CardTitle>Topic Configurations</CardTitle>
          <CardDescription>Configure Bloom level for each topic</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {configs.map((config, idx) => (
            <div key={idx} className="p-4 border border-gray-200 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <Badge variant="secondary">Topic {idx + 1}</Badge>
                <button
                  onClick={() => handleRemoveConfig(idx)}
                  className="p-1 text-red-600 hover:bg-red-50 rounded"
                >
                  <Trash2 size={18} />
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Topic</label>
                <Select
                  value={config.topic}
                  onChange={(e) => handleConfigChange(idx, 'topic', e.target.value)}
                >
                  <option value="">Select a topic</option>
                  {syllabus?.topics?.map((topic) => (
                    <option key={topic.name} value={topic.name}>
                      {topic.name}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Bloom Level</label>
                <Select
                  value={config.bloom_level}
                  onChange={(e) => handleConfigChange(idx, 'bloom_level', e.target.value)}
                >
                  {BLOOM_LEVELS.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Questions</label>
                  <Input
                    type="number"
                    value={config.num_questions}
                    onChange={(e) => handleConfigChange(idx, 'num_questions', parseInt(e.target.value))}
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Marks Each</label>
                  <Input
                    type="number"
                    value={config.marks_per_question}
                    onChange={(e) => handleConfigChange(idx, 'marks_per_question', parseInt(e.target.value))}
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Difficulty</label>
                  <Select
                    value={config.difficulty}
                    onChange={(e) => handleConfigChange(idx, 'difficulty', e.target.value)}
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </Select>
                </div>
              </div>
            </div>
          ))}

          <Button onClick={handleAddConfig} variant="outline" className="w-full">
            <Plus size={18} className="mr-2" />
            Add Topic
          </Button>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={handleSubmit} disabled={submitting} className="flex-1">
          {submitting ? 'Creating blueprint...' : 'Create Blueprint & Generate Questions'}
        </Button>
        <Button variant="outline" onClick={() => navigate('/dashboard')}>
          Cancel
        </Button>
      </div>
    </div>
  )
}

export default BloomConfig
