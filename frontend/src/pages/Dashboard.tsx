import { useState, useEffect } from "react"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Badge } from "../components/ui/badge"
import { useVideoStore } from "../store/useVideoStore"
import { Video } from "lucide-react"

export function Dashboard() {
  const [url, setUrl] = useState("")
  const { videos, addVideo, checkStatus } = useVideoStore()

  const handleProcess = () => {
    if (!url) return
    addVideo(url)
    setUrl("")
  }

  // Efeito de Polling para atualizar status
  useEffect(() => {
    const interval = setInterval(() => {
      videos.forEach((video) => {
        if (video.status === 'processing') {
          checkStatus(video.id)
        }
      })
    }, 5000) // Checa a cada 5 segundos

    return () => clearInterval(interval)
  }, [videos, checkStatus])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-2">Gerencie seus vídeos e cortes.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Novo Processamento</CardTitle>
          <CardDescription>Cole o link do vídeo para iniciar.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Input 
              placeholder="https://youtube.com/watch?v=..." 
              className="flex-1"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <Button onClick={handleProcess}>Processar</Button>
          </div>
        </CardContent>
      </Card>

      {videos.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Recentes</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {videos.map((video) => (
              <Card key={video.id} className="overflow-hidden">
                <div className="aspect-video w-full bg-gray-100 flex items-center justify-center">
                  <Video className="h-12 w-12 text-gray-300" />
                </div>
                <CardHeader className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base line-clamp-1">{video.title}</CardTitle>
                    <Badge variant={
                      video.status === 'completed' ? 'success' : 
                      video.status === 'failed' ? 'destructive' : 'warning'
                    }>
                      {video.status === 'processing' ? 'Processando...' : video.status}
                    </Badge>
                  </div>
                  <CardDescription className="line-clamp-1 text-xs">
                    {video.url}
                  </CardDescription>
                  {video.taskId && (
                    <p className="text-[10px] text-gray-400 mt-1">Task ID: {video.taskId}</p>
                  )}
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
