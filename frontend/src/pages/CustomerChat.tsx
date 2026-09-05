import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

interface Customer {
  id: number
  customer_number: string
  name: string
  segment: string
  status: string
}

interface ChatMessage {
  id?: number
  sender: 'customer' | 'assistant' | 'system'
  content: string
  mode?: string | null
  created_at?: string
}

interface Conversation {
  id: number
  ticket_id: number
  ticket_number: string
  customer_name?: string
  subject: string
  status: string
  created_at: string
  updated_at: string
}

function getModeColor(mode: string | null | undefined) {
  if (mode === 'A') return 'bg-green-100 text-green-800'
  if (mode === 'B') return 'bg-yellow-100 text-yellow-800'
  if (mode === 'C') return 'bg-red-100 text-red-800'
  return ''
}

function getModeLabel(mode: string | null | undefined) {
  if (mode === 'A') return 'Mode A — Draft Ready'
  if (mode === 'B') return 'Mode B — Need Information'
  if (mode === 'C') return 'Mode C — Escalated'
  return ''
}

export default function CustomerChatPage() {
  const navigate = useNavigate()
  const [customers, setCustomers] = useState<Customer[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConvId, setActiveConvId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/api/chat/customers')
      .then(r => r.json())
      .then(d => { setCustomers(d.customers || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  const loadConversations = useCallback(async (customerId: number) => {
    const res = await fetch(`/api/chat/conversations/${customerId}`)
    const data = await res.json()
    setConversations(data.conversations || [])
  }, [])

  const selectCustomer = useCallback(async (customer: Customer) => {
    setSelectedCustomer(customer)
    setActiveConvId(null)
    setMessages([])
    await loadConversations(customer.id)
  }, [loadConversations])

  const startNewConversation = useCallback(async () => {
    if (!selectedCustomer) return
    setMessages([])
    const res = await fetch('/api/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: selectedCustomer.id, content: 'Hello, I need help.' }),
    })
    const data = await res.json()
    if (data.conversation_id) {
      setActiveConvId(data.conversation_id)
      setMessages([
        { sender: 'customer', content: 'Hello, I need help.' },
        { sender: 'assistant', content: data.message, mode: data.mode },
      ])
      await loadConversations(selectedCustomer.id)
    }
  }, [selectedCustomer, loadConversations])

  const loadConversation = useCallback(async (conv: Conversation) => {
    setActiveConvId(conv.id)
    const res = await fetch(`/api/chat/messages/${conv.id}`)
    const data = await res.json()
    setMessages(data.messages || [])
  }, [])

  const sendMessage = useCallback(async () => {
    if (!input.trim() || !selectedCustomer || !activeConvId || sending) return
    const content = input.trim()
    setInput('')
    setMessages(prev => [...prev, { sender: 'customer', content }])
    setSending(true)

    try {
      const res = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: selectedCustomer.id,
          conversation_id: activeConvId,
          content,
        }),
      })
      const data = await res.json()
      if (data.message) {
        setMessages(prev => [...prev, { sender: 'assistant', content: data.message, mode: data.mode }])
      }
      await loadConversations(selectedCustomer.id)
    } catch {
      setMessages(prev => [...prev, { sender: 'assistant', content: 'Sorry, something went wrong. Please try again.' }])
    } finally {
      setSending(false)
    }
  }, [input, selectedCustomer, activeConvId, sending, loadConversations])

  if (loading) {
    return <div className="p-8 text-center text-surface-400">Loading customers...</div>
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Left: Customer list + conversations */}
      <div className="w-80 border-r border-surface-200 flex flex-col bg-white">
        <div className="p-3 border-b border-surface-100">
          <h3 className="text-sm font-semibold text-surface-900">Select Customer</h3>
        </div>
        <div className="flex-1 overflow-y-auto">
          {customers.map(c => (
            <button
              key={c.id}
              onClick={() => selectCustomer(c)}
              className={`w-full text-left px-3 py-2 border-b border-surface-50 hover:bg-surface-50 transition-colors ${
                selectedCustomer?.id === c.id ? 'bg-brand-50 border-l-2 border-l-brand-500' : ''
              }`}
            >
              <div className="text-sm font-medium text-surface-900">{c.name}</div>
              <div className="text-xs text-surface-500">{c.customer_number} · {c.segment}</div>
            </button>
          ))}
        </div>

        {selectedCustomer && (
          <div className="border-t border-surface-100 p-3">
            <button
              onClick={startNewConversation}
              className="w-full px-3 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition-colors"
            >
              + New Conversation
            </button>
            {conversations.length > 0 && (
              <div className="mt-2 space-y-1">
                {conversations.slice(0, 5).map(conv => (
                  <button
                    key={conv.id}
                    onClick={() => loadConversation(conv)}
                    className={`w-full text-left px-2 py-1.5 text-xs rounded transition-colors ${
                      activeConvId === conv.id ? 'bg-brand-50 text-brand-700' : 'text-surface-600 hover:bg-surface-50'
                    }`}
                  >
                    <div className="font-medium">{conv.ticket_number}</div>
                    <div className="text-[10px] opacity-70 truncate">{conv.subject || 'Chat conversation'}</div>
                    <div className="flex items-center gap-1 mt-0.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        conv.status === 'resolved' ? 'bg-green-400' :
                        conv.status === 'open' ? 'bg-blue-400' :
                        'bg-surface-300'
                      }`} />
                      <span className="text-[9px] capitalize">{conv.status}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right: Chat area */}
      <div className="flex-1 flex flex-col bg-surface-50">
        {!selectedCustomer ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-3">💬</div>
              <h2 className="text-lg font-semibold text-surface-700">Customer Chat</h2>
              <p className="text-sm text-surface-400 mt-1">Select a customer to start a conversation</p>
            </div>
          </div>
        ) : messages.length === 0 && !activeConvId ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-3">👋</div>
              <h2 className="text-lg font-semibold text-surface-700">Chat with {selectedCustomer.name}</h2>
              <p className="text-sm text-surface-400 mt-1">Click "New Conversation" to start, or select an existing one</p>
            </div>
          </div>
        ) : (
          <>
            {/* Chat header */}
            <div className="px-4 py-2 bg-white border-b border-surface-200 flex items-center justify-between">
              <div>
                <span className="text-sm font-semibold text-surface-900">{selectedCustomer.name}</span>
                <span className="text-xs text-surface-400 ml-2">{selectedCustomer.customer_number}</span>
                {activeConvId && (
                  <button
                    onClick={() => {
                      const conv = conversations.find(c => c.id === activeConvId)
                      if (conv) navigate(`/cases/${conv.ticket_id}`)
                    }}
                    className="text-xs text-brand-600 hover:text-brand-700 font-medium ml-3"
                  >
                    View Case Details →
                  </button>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => navigate('/console')}
                  className="text-xs text-surface-500 hover:text-surface-700 font-medium"
                >
                  Agent Console →
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.sender === 'customer' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[70%] rounded-xl px-4 py-2.5 ${
                    msg.sender === 'customer'
                      ? 'bg-brand-600 text-white'
                      : 'bg-white border border-surface-200 text-surface-800'
                  }`}>
                    {msg.sender === 'assistant' && msg.mode && (
                      <div className={`text-[10px] font-medium px-2 py-0.5 rounded-full mb-1.5 inline-block ${getModeColor(msg.mode)}`}>
                        {getModeLabel(msg.mode)}
                      </div>
                    )}
                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    {msg.created_at && (
                      <div className={`text-[10px] mt-1 ${msg.sender === 'customer' ? 'text-blue-200' : 'text-surface-400'}`}>
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-white border border-surface-200 rounded-xl px-4 py-2.5">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-surface-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-surface-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-surface-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 bg-white border-t border-surface-200">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2.5 text-sm border border-surface-200 rounded-xl bg-surface-50 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                  disabled={sending}
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || sending}
                  className="px-5 py-2.5 text-sm font-medium text-white bg-brand-600 rounded-xl hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
