$(document).ready(function() {

   $('table.tablesorter').tablesorter();

   function play(id) {
     console.log(id)
     var audio = document.getElementById(id);
     audio.play();
   }


   $('form#DisableVouchers select').chosen({
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

   $('select#form-field-vouchers').bind("chosen:no_results", function(e) {
       play('failure');
   });

   $('.chosen-choices > .search-field > input[type=text]').keydown(function (e) {
     if (e.keyCode == 13) {
       $(this).val('');
     }
   });
// MASK
$('input#form-field-mitarbeiter').mask('99999');
$('input#form-field-lehrkraefte').mask('9999');
$('input#form-field-von').mask('99.99.9999', {placeholder:"tt.mm.jjjj"});
$('input#form-field-bis').mask('99.99.9999', {placeholder:"tt.mm.jjjj"});
//$('input#form-field-iban').mask('**99-9999-9999-9999-9999-99', {placeholder:"de99 9999 9999 9999 9999 99"});
$('input#form-field-iban').inputmask({mask:'aa99 9999 9999 9999 9999 99'});
})
