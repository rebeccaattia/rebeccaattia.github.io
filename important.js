
    // Called from your channel code – will run CodeMirror code in the REPL
    window.triggerChannelMessage = (value) => {
      console.log("🎯 Channel trigger:", value);
      if (typeof runEditorInRepl === "function") {
        runEditorInRepl();
      } else {
        console.warn("runEditorInRepl not ready yet.");
      }
    };



    window.onProgramFinished = function() {
      console.log("✅ Program finished (onProgramFinished called)");
      if (window.channel_posttrigger) {
        window.channel_posttrigger();
      }
    };
