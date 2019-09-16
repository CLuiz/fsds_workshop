// Data table constructor
$(function() {
  $('#dataTable').DataTable();
});

// Event handlers
$(function() {
  $("#updateData").click(getAllData(), window.reload())
});

// Include the most common AJAX settings for clarity
function getAllData() {
  $.ajax({
    url: '/refresh_data/',
    beforeSend: function () {
      // Not yet implemented
      // updateModal.show(),
      // glyphicon.spin()
    },
    success:function () {
      //pass
    },
    error: function () {
      //pass
    },
    complete: function () {
      //pass
    },
  })
}


