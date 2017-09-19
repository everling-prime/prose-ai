// place any jQuery/helper plugins in here, instead of separate, slower script files.


/////////////////// cycle display of elements
function cycle_display() {
  var el= document.querySelectorAll('.cycle span'),
      rnd= Math.floor(Math.random() * el.length-1) + 1,
      rnd2= Math.round(Math.random()*20);

  document.querySelector('.cycle span.active').className= '';
  el[rnd].className= 'active';
  //if(rnd2===5) {
  //  setTimeout(cycle_display, 1500);
  //} else {
    setTimeout(cycle_display, 100);
  //}
}
//cycle_display();

/* Example HTML to go with Cycle Display script
<div class="cycle hidden" > <!-- HTML container -->
   <!-- update these values on quill_editor change -->
    <h4>I suggest:</h4>
                <span class="active">walking in circles</span>
                  <span >trying too hard</span>
                  <span >not trying hard enough</span>
                  <span >dancing</span>
                  <span >making strange noises</span>
                  <span >eating a donut</span>
</div>
*/