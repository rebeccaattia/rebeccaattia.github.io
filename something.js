
    const cm = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
      mode:'python', lineNumbers:true, indentUnit:4, smartIndent:true,
    });
    window.code_editor = { editor: cm };

    // Make snippet arguments editable
    function makeArgsEditable(c){
      c.querySelectorAll('.editable-arg').forEach(a=>a.setAttribute('contenteditable','true'));
    }
    const bank = document.getElementById('snippets');
    makeArgsEditable(bank);

    // Drag & drop from snippets to CodeMirror
    bank.querySelectorAll('.snippet').forEach(sn=>{
      sn.addEventListener('dragstart',e=>{
        const codeOnly=sn.cloneNode(true);
        const expl=codeOnly.querySelector('.snippet-expl');
        if(expl) expl.remove();
        e.dataTransfer.setData('text/plain',codeOnly.textContent.trim());
      });
    });

    cm.getWrapperElement().addEventListener('dragover',e=>e.preventDefault());
    cm.getWrapperElement().addEventListener('drop',e=>{
      e.preventDefault();
      let snippetText=e.dataTransfer.getData('text/plain').trim();
      if(snippetText.startsWith('for ')){
        snippetText+='\n    # Indent code you want to loop\n    print("This repeats!")';
      }
      cm.replaceSelection((cm.getValue()?'\n':'')+snippetText);
      cm.focus();
    });

    // Local storage autosave
    const STORAGE_KEY="student_workspace_code";
    const saved=localStorage.getItem(STORAGE_KEY);
    if(saved) cm.setValue(saved);

    document.getElementById('saveCode').addEventListener('click',()=>{
      localStorage.setItem(STORAGE_KEY,cm.getValue());
      alert("✅ Code saved!");
    });

    document.getElementById('clearCode').addEventListener('click',()=>{
      if(confirm("Clear your code?")){
        cm.setValue("");
        localStorage.removeItem(STORAGE_KEY);
      }
    });

    setInterval(()=>localStorage.setItem(STORAGE_KEY,cm.getValue()),10000);

    document.getElementById('downloadCode').addEventListener('click',()=>{
      const blob=new Blob([cm.getValue()],{type:'text/x-python'});
      const link=document.createElement('a');
      link.href=URL.createObjectURL(blob);
      link.download='my_program.py';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });

    // Turn sync code into async-friendly for REPL
    function transformCodeForAsync(code){
      // Replace blocking time.sleep() with asyncio.sleep()
      code = code.replace(/\btime\.sleep\((.*?)\)/g,"await asyncio.sleep($1)");

      // Indent user code for the async function
      const userIndented = code
        .split('\n')
        .map(l => '    ' + l)
        .join('\n');

      // Build the async wrapper and call window.onProgramFinished at the end
      const funcDef =
`import asyncio
from pyscript import window

async def _user_program():
${userIndented}

    try:
        window.onProgramFinished()
    except Exception as e:
        print("onProgramFinished error:", e)
`;

      const runner =
`loop = asyncio.get_event_loop()
loop.create_task(_user_program())
`;

      return {funcDef, runner};
    }

    function sendToRepl(parts){
      const term=document.getElementById('python-terminal');
      if(!term?.process) return false;
      try{
        term.process("\x03"); // Ctrl-C to clear any running program
        for(const line of parts.funcDef.split("\n")){
          if(line.trim()) term.process(line+"\n");
        }
        term.process("\n"+parts.runner+"\n");
        return true;
      }catch(e){
        console.error("REPL send error:",e);
        return false;
      }
    }

    // ======== AUTO-SCROLL FLAG ========
    let autoScrollRepl = true;

    function runEditorInRepl(){
      const raw=cm.getValue().trim();
      if(!raw) return;
      autoScrollRepl = true;   // re-enable autoscroll each time we run
      sendToRepl(transformCodeForAsync(raw));
    }
    window.runEditorInRepl = runEditorInRepl; // so triggerChannelMessage can see it

    document.getElementById('REPLRun').addEventListener('click',runEditorInRepl);
    cm.addKeyMap({"Shift-Enter":()=>runEditorInRepl()});

    // Clear REPL
    document.getElementById('clearRepl').addEventListener('click',()=>{
      const term=document.getElementById('python-terminal');
      if(term?.terminal?.clear) term.terminal.clear();
      else if(term?.terminal?.write) term.terminal.write('\x1bc');
      autoScrollRepl = true;  // after clearing, autoscroll to new output
    });

    // Pre-import time & asyncio once terminal is ready
    window.addEventListener('load',()=>{
      const term=document.getElementById('python-terminal');
      const autoImport=setInterval(()=>{
        if(term && typeof term.process==='function'){
          term.process('import time\n');
          term.process('import asyncio\n');
          clearInterval(autoImport);
        }
      },500);
    });

    // Reveal hub2 when Add More clicked (guarded so it won't error if button is commented out)
    const addMoreBtn = document.getElementById("addMoreBtn");
    if (addMoreBtn) {
      addMoreBtn.onclick = () => {
        const hub2 = document.getElementById("hub2");
        if (hub2) {
          hub2.style.display = "block";
        }
      };
    }

    // ========= SMART REPL AUTOSCROLL (polling-based, shadow-DOM safe) =========
    const replContainer = document.getElementById("replContainer");
    const SCROLL_THRESHOLD = 10;

    if (replContainer) {
      // If the user scrolls up, pause autoscroll until they scroll back to bottom
      replContainer.addEventListener('scroll', () => {
        const distanceFromBottom =
          replContainer.scrollHeight -
          replContainer.scrollTop -
          replContainer.clientHeight;
        autoScrollRepl = distanceFromBottom < SCROLL_THRESHOLD;
      });

      // Periodically snap to bottom while autoscroll is enabled
      setInterval(() => {
        if (!autoScrollRepl) return;
        replContainer.scrollTop = replContainer.scrollHeight;
      }, 200);
    }
