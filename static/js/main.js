// Data table constructor
$(function() {
  $('#dataTable').DataTable();
});

// Event handlers
$(function () {
  $("#refreshData").click(getAllData)
});

// set up datetimepicker
 $(function () {

   var dateFormat = "MM-DD-YYYY";
   var minDate = "01-01-2015";
   var maxDate = "01-01-2025";

   dateMin = moment(minDate, dateFormat);
   dateMax = moment(maxDate, dateFormat);

   $('#datetimepicker1').datetimepicker({
     format: 'YYYY',
     minDate: dateMin,
     maxDate: dateMax,
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


