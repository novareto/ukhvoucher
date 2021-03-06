
$(document).ready(function() {

    $('form#DisableVouchers select').select2({
        tags: false,
        multiple: true,
        language: "de",
        tokenSeparators: [',', ' '],
    })

    $('table.tablesorter').tablesorter();

    function play(id) {
        var audio = document.getElementById(id);
        audio.play();
    }


    $('select#form-field-date_range').change(function() {
     $('input#form-action-cdr').click();
    })

    var selected_vouchers = $("<div id='selected_vouchers'></div>")
    $("#field-form-field-vouchers").append(selected_vouchers);

    function update_selected(id) {
        let selected = $(id).val() || [];
        selected_vouchers.text(selected.length + ' Berechtigungsschein(e) ausgewählt');
    }

    $("#field-form-field-vouchers").on('select2:unselect', function(evt) {
        $("select#form_field_vouchers option[value='" + evt.params.data.id + "']").remove();
        update_selected('select#form_field_vouchers')
        play("failure");
    });

    $("#field-form-field-vouchers").on('select2:select', function(evt) {
        console.log(evt)
        update_selected('select#form_field_vouchers')
        play("success");
    });

    // MASKS
    $('input#form-field-mitarbeiter').mask('99999');
    $('input#form-field-lehrkraefte').mask('9999');
    $('input#form-field-von').mask('99.99.9999', {placeholder:"tt.mm.jjjj"});
    $('input#form-field-bis').mask('99.99.9999', {placeholder:"tt.mm.jjjj"});
    $('input#form-field-abis').mask('99.99.9999', {placeholder:"tt.mm.jjjj"});
    //$('input#form-field-iban').mask('**99-9999-9999-9999-9999-99', {placeholder:"de99 9999 9999 9999 9999 99"});
    $('input#form-field-iban').inputmask({
        mask: 'aa99 9999 9999 9999 9999 99'
    });
})
