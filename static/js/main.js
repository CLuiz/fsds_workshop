// Data table constructor
$(function() {
  $('#dataTable').DataTable();
});

// Event handlers
$(function() {
  $("#refreshData").click(getAllData())
});

// Include the most common AJAX settings for clarity
function getAllData() {
  $.ajax({
    url: '/refresh_data/',
    beforeSend: function () {
      // Not yet implemented
      // glyphicon.spin()
    },
    success:function () {
      //pass
      console.log('Sweet success')
    },
    error: function () {
      //pass
    },
    complete: function () {
      console.log('Complete!')
      //pass
    },
  })
}


