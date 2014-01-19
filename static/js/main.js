

$(document).ready(function() {

	$(".clickable").click(function(e) {
		alert('Clicked!');
		$.post("/select", {value1:"fhsdjfh"}, function(data) {
			console.log(data);
			
		})

	});

});