M.AutoInit();
// 
// function base_exec(id, func) {
//
//   function search() {
//     var name = $("#search").val();
//     $("search").val("");
//
//     $.ajax({
//       method: 'POST',
//       url: {{ url_for('search') | tojson }}
//       data: {
//         'name' : name
//       }
//     }).done(searchShow);
//   }
//   function searchShow(data) {
//     console.log(data.r);
//   }
//
//
// }
