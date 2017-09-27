//<!-- Main Quill library -->
//<script src="//cdn.quilljs.com/1.3.2/quill.js"></script>
//<script src="//cdn.quilljs.com/1.3.2/quill.min.js"></script>

require('quill');



var toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike'],        // toggled buttons
  ['blockquote', 'code-block'],

  [{ 'header': 1 }, { 'header': 2 }],               // custom button values
  [{ 'list': 'ordered'}, { 'list': 'bullet' }],
  //[{ 'script': 'sub'}, { 'script': 'super' }],      // superscript/subscript
  //[{ 'indent': '-1'}, { 'indent': '+1' }],          // outdent/indent
  //[{ 'direction': 'rtl' }],                         // text direction

  [{ 'size': ['small', false, 'large', 'huge'] }],  // custom dropdown
  [{ 'header': [1, 2, 3, 4, 5, 6, false] }],

  [{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
  [{ 'font': [] }],
  [{ 'align': [] }],

  ['clean'],                                         // remove formatting button
  ['omega']
];
 

// Quill Editor options
var options = {
  debug: 'info',
  modules: {
    counter: true,
    toolbar: toolbarOptions
  },
  placeholder: 'Enter a few words...',
  theme: 'snow'
};
    
//     CREATE QUILL      //
var quill = new Quill('#quill_editor', options);
    
$.get('/editor/load_contents', function(delta_response) {
       var load = new Delta(JSON.parse(delta_response));
       quill.setContents(load);
       });
 
    
// Store accumulated changes
var Delta = Quill.import('delta');
var change = new Delta();
quill.on('text-change', function(delta) {
  change = change.compose(delta);
});


// Save periodically
setInterval(function() {
  if (change.length() > 0) {
    console.log('Saving changes', change);
      
    /* 
    //Send partial changes
    $.post('/editor/save_delta', { 
      partial: JSON.stringify(change) 
    });
    */
    
    
    //Send entire document
    $.getJSON('/editor/save_contents', { 
      contents: JSON.stringify(quill.getContents()) 
    });
    
    
    change = new Delta();
  }
}, 5*1000);

// Check for unsaved data
window.onbeforeunload = function() {
  if (change.length() > 0) {
    return 'There are unsaved changes. Are you sure you want to leave?';
  }
  //if (proseai.status === 'alive') {
  //  return 'Are you sure you want to leave this page? Prose AI will be killed.';    
  //}
}

// DROPDOWN SELECT OUTPUT TO DISPLAY
$(document).ready(function(){
    $("select").change(function(){
        $(this).find("option:selected").each(function(){
            var optionValue = $(this).attr("value");
            
            if(optionValue){
                if(optionValue=='all_help'){
                    $(".output").show();
                } else { 
                $(".output").not("." + optionValue).hide();
                $("." + optionValue).show();
                }
            } else{
                $(".output").hide();
            }
        });
    }).change();
});


 








$(function catch_quill_change() {
  $('div#quill_editor').on("change keyup", function() {      
    // to python backend API  
    $.getJSON('/editor/textproc/', {
      content: quill.getText(),
    }, function(response_data) {
      // Update output elements
      $("#entities").html(response_data.ents); 
      $("#other").html(response_data.other);
        
      
    });
    return false;
  });
});

// Gets extractive summary
$(function summarize() {
  $('button#summarize').on("click", function() {
     $("#summary").empty();
     $("#summary").addClass("spinner");
    // to python backend API  
    $.getJSON('/editor/textproc/summarize', {
      content: quill.getText(),
    }, function(response_data) {
      $("#summary").html("<b>SUMMARY:</b><br>"+response_data.summary+"<br><hr>"); //update summary
      var readability = response_data.readability //JSON object of readability scores
      var readability_ease = readability['flesch_readability_ease']
      //$("#readability").text(JSON.stringify(readability_ease));
      $("#readability").removeClass("hidden");
      $("#reada_header").removeClass("hidden");
      $("#summary").removeClass("spinner");
    });
    return false;
  });
});
    
// checks #entities list every few seconds and tries to turn them into wikipedia links
/*
setInterval(function() {
    $('#entities').text(function() {
        $.getJSON('/editor/textproc/linkify', {
          ents: $('#entities').text(),
        }, function(response_data) {
          $("#linkified_entities").html(response_data.linkified_ents); //update Output
              //response_data.suggestions //update cycle's span items 
        });
    });
}, 3000);
*/
 
setInterval(function keyterm_check() {
    //if (change.length() > 0) {
        $('#quill_editor').text(function() {
            $.getJSON('/editor/textproc/get_keyterms', {
              content: quill.getText(),
            }, function(response_data) {
              $("#extracted_topics").html("<br>"+response_data.keyterms);
            });
        });
    //};
}, 5000);

setInterval(function completion_check() {
    $('#quill_editor').text(function() {
        $.getJSON('/editor/textproc/completions', {
          content: quill.getText(),
        }, function(response_data) {
          $("#completions").empty();
          if (response_data.completions) {
              var completions = response_data.completions;
              completions.forEach(function(compl){
                 $("#completions").append(compl
                                         +"<hr>");
                 //$("#completions_header").text()
                 });
              };
        });
    });
}, 5000);

//  $('div#quill_editor').on("change keyup", function() {   
//$('button#lint').on("click", function () { 
$(function() {
  $('button#lint').on("click", function lint () {
        $("#proselints").empty();
        $("#proselints").addClass("spinner");
        $.getJSON('/editor/textproc/lint_prose', {
            content: quill.getText(),
        }, function(response_data) {
            
            $("#proselints").removeClass("spinner");
            var suggestions = response_data.proselint_suggestions;
            if (!suggestions[0]) { $("#proselints").text("Looks good!") };
            suggestions.forEach(function (sugg){ 
                //sugg = {check, message, line, column, start, end, extent, severity, replacements} 
                var sugg_replacements = sugg.replacements //usually null
                if (!sugg.replacements) { sugg_replacements = "" };
                
                $("#proselints").append('Found "',
                                        sugg.check + '" -- ',
                                        sugg.message + 
                                        '<br>' + sugg_replacements + 
                                        '<hr>');
                
                quill.formatText(sugg.start-1, sugg.extent-1, 'background-color', '#FED766');  
            } );
            
            $("#hide_lints").removeClass("hidden");
            var lint = lint;
        });
      
    });
});



var idleTime = 0;
$(document).ready(function () {
    //Increment the idle time counter every minute.
    var idleInterval = setInterval(timerIncrement, 1000); // 1 second

    //Zero the idle timer on mouse movement.
    $(this).mousemove(function (e) {
        idleTime = 0;
    });
    $(this).keypress(function (e) {
        idleTime = 0;
    });
});

function timerIncrement() {
    idleTime = idleTime + 1;
    if (idleTime > 60) { // 60 seconds
              
        $.getJSON('/editor/textproc/lint_prose', {
            content: quill.getText(),
        }, function(response_data) {
            $("#proselints").empty();
            var suggestions = response_data.proselint_suggestions;
            if (!suggestions[0]) { $("#proselints").text("Looks good!") };
            suggestions.forEach(function (sugg){ 
                //sugg = {check, message, line, column, start, end, extent, severity, replacements} 
                var sugg_replacements = sugg.replacements //usually null
                if (!sugg.replacements) { sugg_replacements = "" };
                
                $("#proselints").append('Found "',
                                        sugg.check + '" -- ',
                                        sugg.message + 
                                        '<br>' + sugg_replacements + 
                                        '<hr>');
                
                quill.formatText(sugg.start-1, sugg.extent-1, 'background-color', '#FED766');  
            } );
            
            $("#hide_lints").removeClass("hidden");
            var lint = lint;
        });
        
    }
}  





document.getElementById("hide_lints").onclick = 
    function hide_lints() {       
    quill.formatText(0, quill.getLength(), 'background-color', 'white');
    $("#proselints").empty();
    $("#hide_lints").addClass("hidden");
};


/*
$("#quill_editor").focusin(function() {
    $(".a-eye").fadeIn();
}).focusout(function () {
    $(".a-eye").fadeOut();
});
*/

// Make spinner active only on editor focus
/*
$("#quill_editor").focusin(function trigger_spinner() {
    $("#avatar").addClass("spinner");
}).focusout(function () {
    $("#avatar").removeClass("spinner");
});
*/
