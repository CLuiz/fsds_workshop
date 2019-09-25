// Data table constructor
$(function() {
  $('#dataTable').DataTable();
});

// Event handlers
$(function () {
  $("#refreshData").click(getAllData)
});

$(function () {
  $("a[name=yearOption]").on("click", function () {
    var year = $(this).attr("data-value");
    console.log(year);
    switchYear(year);
});
});

// Include the most common AJAX settings for clarity
function getAllData() {
  $.ajax({
    url: '/refresh_data/',
    beforeSend: function () {
      // Not yet implemented
      // glyphicon.spin()
      console.log('refresh data called');
    },
    success: function () {
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

function switchYear(year) {
  $.ajax({
    url: '/switch_year/',
    type: 'POST',
    data: {'year': year},
    beforeSend: function () {
      // Not yet implemented
      // glyphicon.spin()
      console.log('Switch year ajax called');
    },
    success: function () {
      //pass
      console.log('Sweet success')
      location.reload()
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

