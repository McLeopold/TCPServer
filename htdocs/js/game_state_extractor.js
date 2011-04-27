function game_state_extractor() {
   var povSelectorString = '<select id="me_povSelector" style="margin:10px;"></select>';
   var refreshButton = '<input id="me_refresh" type="Submit" value="Refresh" style="margin-left:200px;"/>';
   var povContainerString = '<p>Point of view: ' + povSelectorString + refreshButton + '</p>';
   var textAreaString = '<textarea id="me_mapState" cols="80" rows="30"' +
                  ' style="margin-top: 10px;"></textarea>';
   var formString = '<form>' + povContainerString + textAreaString + '</form>';
   
   $("#visualizer").append(formString);
   var povSelector = $('#me_povSelector');
   var refreshButton = $("#me_refresh");
   var mapElement = $('#me_mapState');

   povSelector.append('<option value="1">' + Visualizer.players[0] + '</option>');
   povSelector.append('<option value="2">' + Visualizer.players[1] + '</option>');
   
   var mapElement = $('#me_mapState');
   
   povSelector.change(function() {
      var pov = $(this).val();
      var mapText = "";
      
      var planets = Visualizer.planets;
      var numPlanets = planets.length;
      
      for (var p = 0; p < numPlanets; p++) {
         var planet = planets[p];
         var actual_owner = planet.owner;
         var pov_owner = 0;
         
         if (actual_owner != 0) {
            pov_owner = (pov == actual_owner ? 1 : 2);
         }
         
         mapText += "P " + planet.x + " " + planet.y + " " + pov_owner +
                  " " + planet.numShips + " " + planet.growthRate + "\n";
      }
      
      var frame = Math.floor(Visualizer.frame);
      var fleets = Visualizer.moves[frame].moving;
      
      var numFleets = fleets.length;
      var i = 0;
      
      for (var f = 0; f < numFleets; f++) {
         var fleet = fleets[f];
         var actual_owner = fleet.owner;
         var pov_owner = (pov == actual_owner ? 1 : 2);

         var sourceX = fleet.source.x;
         var sourceY = fleet.source.y;
         var destinationX = fleet.destination.x;
         var destinationY = fleet.destination.y;
         
         var source = -1;
         var destination = -1;
         var foundSource = false;
         var foundDestination = false;
         
         for (i = 0; i < numPlanets; i++) {
            var planet = planets[i];
            if (planet.x == sourceX && planet.y == sourceY) {
               source = i;
            
            } else if (planet.x == destinationX && planet.y == destinationY) {
               destination = i;
            }
         }

         mapText += "F " + pov_owner + " " + fleet.numShips + " " +
                  source + " " + destination + " " + fleet.tripLength +
                  " " + (fleet.tripLength - fleet.progress) + "\n";
      }

      mapElement.text(mapText);
   });

   refreshButton.click(function() {
      povSelector.change();
      return false;
   });
   
   povSelector.change();
};  