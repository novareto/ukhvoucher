$(document).ready(function() {

   function play(id) {
     var audio = document.getElementById(id);
     audio.play();
   }
   
   $('select').chosen({
	placeholder_text_multiple: 'Bitte wählen Sie die Berechtigungsscheine',
	placeholder_text_single: 'Bitte wählen Sie eine Begründung aus',
    width: '555px',
    max_shown_results: 5,
    min_length: 5,
}
);

   $('select#form-field-vouchers').on('change', function(evt, params) {
       console.log(evt);
       console.log(params);
       console.log(params.selected);
       play("success");
   });

   $(document).bind("chosen:no_results", function(e) {
       play('failure');
   });

   $('.chosen-choices > .search-field > input[type=text]').keydown(function (e) {
     if (e.keyCode == 13) {
       $(this).val('');
     }
   });

})
