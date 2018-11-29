
function uploadProfilePicture(mID) {
    var formdata = new FormData();
    var file = document.getElementById('regprofileimage'+mID).files[0];
    formdata.append('profileimage', file);
    formdata.append('csrfmiddlewaretoken', $('input[name=csrfmiddlewaretoken]').val());
    $.ajax({

        type: 'POST',
        url: '/profile/'+mID+'/uploadimage/',
        data:formdata,
        success: function (data) {
            alert('image uploaded')
        },
        processData: false,
        contentType: false
    });
}

