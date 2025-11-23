Título: System.ArgumentOutOfRangeException em PSReadLine.ReallyRender — parâmetro `top` = -128 ao inserir texto multilinha (here-string + git rebase)

Resumo
- Ao digitar/colocar um bloco multilinha (here-string seguido por comandos git) no PowerShell com PSReadLine, a sessão lança System.ArgumentOutOfRangeException em Microsoft.PowerShell.PSConsoleReadLine.ReallyRender, com `top = -128`. O PSReadLine então trava a entrada.

Ambiente
- SO: Windows
- Shell: Windows PowerShell 5.1
- Biblioteca: PSReadLine (versão não fornecida)

Trecho relevante do erro / stack trace
System.ArgumentOutOfRangeException: O valor deve ser maior ou igual a zero e menor que o tamanho do buffer do console nessa dimensão.
Nome do parâmetro: top
Valor real era -128.
   em System.Console.SetCursorPosition(Int32 left, Int32 top)
   em Microsoft.PowerShell.PSConsoleReadLine.ReallyRender(RenderData renderData, String defaultColor)
   em Microsoft.PowerShell.PSConsoleReadLine.ForceRender()
   em Microsoft.PowerShell.PSConsoleReadLine.Insert(Char c)
   em Microsoft.PowerShell.PSConsoleReadLine.SelfInsert(Nullable`1 key, Object arg)
   em Microsoft.PowerShell.PSConsoleReadLine.ProcessOneKey(ConsoleKeyInfo key, Dictionary`2 dispatchTable, Boolean ignoreIfNoAction, Object arg)
   em Microsoft.PowerShell.PSConsoleReadLine.InputLoop()
   em Microsoft.PowerShell.PSConsoleReadLine.ReadLine(Runspace runspace, EngineIntrinsics engineIntrinsics)

Últimas ~200 teclas (fornecido pelo usuário)
- (trecho preservado na íntegra pelo usuário; omito repetição)

Contexto / passos que parecem ter levado ao problema
1. O usuário estava colando um here-string grande no PowerShell e salvando com `Set-Content`:
   Ex.: `... $content = @' ... '@; Set-Content -Path 'backend/src/main.py' -Value $content -Encoding UTF8; ...`
2. Em seguida executou comandos git (`git add`, `git rebase --continue`) ou similares no mesmo prompt.
3. PSReadLine tentou re-renderizar o buffer enquanto a entrada continha muitas linhas; durante o `Insert`/render ocorreu SetCursorPosition com `top = -128`, fora dos limites do buffer.

Comandos de diagnóstico sugeridos (cole saídas no issue):
Get-Module -ListAvailable PSReadLine | Select-Object Name, Version, Path
$PSVersionTable
Get-Host
[console]::BufferHeight
[console]::WindowHeight
[console]::BufferWidth
[console]::CursorTop
[console]::CursorLeft

Reprodução mínima (sugestão)
- Abrir PowerShell 5.1 com PSReadLine carregado.
- Colar um here-string grande seguido por uma sequência de comandos em uma única entrada, por exemplo:
  $content = @'
  (várias linhas de código)
  '@; Set-Content -Path 'backend/src/main.py' -Value $content -Encoding UTF8; git add backend/src/main.py; git rebase --continue
- Verificar se PSReadLine lança a exceção durante a colagem ou inserção.

Mitigações temporárias
- Remove-Module PSReadLine
- Usar PowerShell Core (`pwsh`) ou outro host
- Evitar colar blocos multilinha muito grandes diretamente no prompt

Instruções para anexar saídas e submeter
- Abra https://github.com/lzybkr/PSReadLine/issues/new e cole este conteúdo.
- Anexe saídas dos comandos de diagnóstico listados acima.

Obrigado! Se quiser, posso commitar este arquivo e empurrar para um branch remoto.
