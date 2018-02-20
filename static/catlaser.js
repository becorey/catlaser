$(document).ready(function(){
	$('#clickbox').click(function(e){
		var offset = $(this).offset();
		var x = ((e.pageX - offset.left)/$(this).width()).toFixed(4)-0.5;
		var y = ((e.pageY - offset.top)/$(this).height()).toFixed(4);
		$.get("clicked?x="+x+"&y="+y, function(data, status){
			
		});
	});
	
});
