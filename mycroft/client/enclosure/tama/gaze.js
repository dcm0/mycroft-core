'use strict';

const path = require('path');
var HEAD=true;
var test_mode=false;
var gaze=true;
var test_timeout=140;
var test_counter=0;
var verbose=false;
var googleAssistant=true;
var cam_connected=false;
var speaking_L=false;
var speaking_R=false;
var head_started=false;
var cancel_convesation_L=0;
var cancel_convesation_R=0;
var gaze_L_counter=0;
var gaze_R_counter=0;
var GAZE_LIMIT=1;
var abort=8;
var time_next_ready=800;
var onStatus="starting";
var update_pos;
var pictures=false;
var project_path='default';
var save_log=false;
var pixel_ring_ON=false;
var google_json = {}; // empty Object
var tama_json = {}; // empty Object
var cam_L_json = {}; // empty Object
var cam_R_json = {}; // empty Object
var config_json = {}; // empty Object
var gaze_json = {}; // empty Object
var start_time=Date.now();
var number_gaze_interacitons=0;
var number_stopped_gaze_interacitons=0;
var number_requests=0;


// print process.argv
process.argv.forEach(function (val, index, array) {
    if (val=='nohead') HEAD=false;
    if (val=='nogaze') gaze=false;
    if (val=='pictures') pictures=true;
    if (val.indexOf('Test') >= 0){
        project_path=val;
        save_log=true;
        console.log('The project name is: '+project_path);
    }
    if (val=='pixelring') pixel_ring_ON=true;
    console.log(index + ': ' + val);
});
if (!save_log) pictures=false;


async function sendToBus(message){
	//Message should look like: speak '{"utterance":"hello"}'
	message = "mycroft.messagebus.send "+message;
	PythonShell.runString(message, null, function (err) {
	  if (err) throw err;
	  console.log('finished');
	});
}


if (save_log){
    ensureExists(__dirname + '/'+project_path, 484, function(err) {
    if (err) console.log('Cannot create folder: '+err);// handle folder creation error
    //else // we're all good
    });
}


// Load the node-omron-hvc-p2 and get a `HvcP2` constructor object
const HvcP2_R = require('node-omron-hvc-p2');
const HvcP2_L = require('node-omron-hvc-p2');

// Create a `HvcP2` object
//const hvcp2_R = new HvcP2_R();
//const hvcp2_L = new HvcP2_L();

console.log('HvcP2 created');

async function detectFor_R(){
    //Needs to be in an async function to use await
	var startTime = Date.now();
    var get_picture=false;
    var res_json;
        
    while (true) {
	
    startTime = Date.now();
    if ((get_picture==true)&&(pictures)){
            await hvcp2_R.detect({
                face: 1,
                direction: 1,
                age: 1,
                gender: 1,
                gaze: 1,
                expression: 1,
                image: 1,            // Enable capturing image
                imageType   : 3,            // Save the image as a file
                imageFormat : 'png',        // Image format
                imagePath   : './'+project_path+'/'+project_path+startTime+'R.png', // File path
                imageMarker : true          // Draw markers in the image
	  }).then((res) => {
            res_json=res;
            get_picture=false;
  	  }).catch((error) => {
  	    console.error('R ' + error);
 	   	//  pixelshell.send('RED');
		sendToBus('enclosure.eyes.spin');
        process.exitCode = 1;
  	  });
      }else {
            await hvcp2_R.detect({
                face: 1,
                direction: 1,
                age: 1,
                gender: 1,
                gaze: 1,
                expression: 1
	  }).then((res) => {
          res_json=res;
  	  }).catch((error) => {
  	    console.error(error);
//        pixelshell.send('RED');
		sendToBus('enclosure.eyes.spin');
        process.exitCode = 1;
  	  });}
		
		
		if(res_json["face"].length > 0){
            if (save_log) log_data(res_json,cam_R_json);
            
			for (var i=0;i<res_json["face"].length;i++){
                var yaw=res_json["face"][i]["gaze"]["yaw"];
                var pitch=res_json["face"][i]["gaze"]["pitch"];
                if (pitch<10&&pitch>-2&&yaw<5&&yaw>-5){
                    if (save_log) log_data("R",gaze_json);
                    if (speaking_L==false&&speaking_R==false) gaze_R_counter++;
                    var x=res_json["face"][i]["face"]["x"];
                    var y=res_json["face"][i]["face"]["y"];
                    var [x_sign,x_m,y_sign,y_m]=getdeg(x,y);
                    x_m = x_m - 15;//15 = camera offset angle
                    x_m=Math.abs(x_m);
                    y_m=Math.abs(y_m);
                    update_pos='MOVE:'+x_sign+":"+x_m+":"+y_sign+":"+y_m+":\n";
					data = '{"data":'+update_pos+'}';
					sendToBus('enclosure.eyes.right '+update_pos);
                    
                    cancel_convesation_R=0;
                    
                }else {
                    gaze_R_counter=0;
                    if (cancel_convesation_R==abort){
                            sendToBus('enclosure.eyes.right_cancel');
                    }
                    cancel_convesation_R++;
                    
                }
            }
			
		}else{
            gaze_R_counter=0;
			cancel_convesation_R++;
		}

    }//While
}
async function detectFor_L(){
	//Needs to be in an async function to use await
	var startTime = Date.now();
    var get_picture=false;
    var res_json;
        
    while (true) {
        startTime = Date.now();
        if ((get_picture==true)&&(pictures)){
        await hvcp2_L.detect({
            face: 1,
            direction: 1,
            age: 1,
            gender: 1,
            gaze: 1,
            expression: 1,
            image: 1,            // Enable capturing image
            imageType   : 3,            // Save the image as a file
            imageFormat : 'png',        // Image format
            imagePath   : './'+project_path+'/'+project_path+startTime+'L.png', // File path
            imageMarker : true          // Draw markers in the image
	  }).then((res) => {
          res_json=res;
            get_picture=false;
  	  }).catch((error) => {
  	    console.error(error);
		sendToBus('enclosure.eyes.spin');
        process.exitCode = 1;
            
  	  });
        }else {
            await hvcp2_L.detect({
                face: 1,
                direction: 1,
                age: 1,
                gender: 1,
                gaze: 1,
                expression: 1
	  }).then((res) => {
          res_json=res;
  	  }).catch((error) => {
  	    console.error(error);
		sendToBus('enclosure.eyes.spin');
        process.exitCode = 1;
  	  });
        }
            
        if(res_json["face"].length > 0){
            if (save_log) log_data(res_json,cam_L_json);
            for (var i=0;i<res_json["face"].length;i++){
                var yaw=res_json["face"][i]["gaze"]["yaw"];
                var pitch=res_json["face"][i]["gaze"]["pitch"];
                if (pitch<10&&pitch>-2&&yaw<5&&yaw>-5){
                    if (save_log) log_data("L",gaze_json);
                    if (speaking_L==false&&speaking_R==false) gaze_L_counter++;
                    var x=res_json["face"][i]["face"]["x"];
                    var y=res_json["face"][i]["face"]["y"];
                    var [x_sign,x_m,y_sign,y_m]=getdeg(x,y);
                    x_m = x_m + 15;//15 = camera offset angle
                    x_m=Math.abs(x_m);
                    y_m=Math.abs(y_m);
					update_pos='MOVE:'+x_sign+":"+x_m+":"+y_sign+":"+y_m+":\n";
					data = '{"data":'+update_pos+'}';
					sendToBus('enclosure.eyes.left '+update_pos);
				    cancel_convesation_L=0;
                    
                }else {
                    gaze_L_counter=0;
                    if (cancel_convesation_L==abort){
						sendToBus('enclosure.eyes.left_cancel');
                    }
                    cancel_convesation_L++;
                }
            }
		}else{
            gaze_L_counter=0;
		    cancel_convesation_L++;
		}
        
    }//While
}

    hvcp2_R.connect({
        path: '/dev/ttyACM0'
    }).then(() => {
    console.log('HVC Cam R ready');
    hvcp2_R.setConfigurations({
        cameraAngle: {
            angle: 0 // Camera angle: 270º
        }
    }).then((res) => {
        detectFor_R();
    }).catch((error) => {
        console.error(error);
    });
    
    }).catch((error) => { //connect
    console.error(error);
    });

    hvcp2_L.connect({
    path: '/dev/ttyACM1'
    }).then(() => {
        console.log('HVC Cam L ready');
        hvcp2_L.setConfigurations({
        cameraAngle: {
            angle: 0 // Camera angle: 270º
        }
    }).then((res) => {
        detectFor_L();
    }).catch((error) => {
        console.error(error);
    });
    }).catch((error) => { //connect
        console.error(error);
    });
function getdeg(x,y) {
    x -= 800;
    y -= 600;
    var x_=1;
    var y_=1;
    var x_pos = (Math.atan(x * Math.tan(27 * Math.PI / 180) / 800)) * 180 / Math.PI;//HVC spec X: -27deg to 27deg
    var y_pos = 15-(Math.atan(y * Math.tan(20.5 * Math.PI / 180) / 600)) * 180 / Math.PI;//HVC spec Y:-20.5deg to 20.5deg
    if (x<0) x_=-1;
    if (y<0) y_=-1;
    return [x_,Math.round(x_pos), y_, Math.round(y_pos)];
}

process.on("SIGINT", () => {

    if (save_log) save_json(google_json,'assistant');
    if (save_log) save_json(cam_L_json,'cam_L');
    if (save_log) save_json(cam_R_json,'cam_R');
    if (save_log) log_config_file(config_json);
    if (save_log) save_json(config_json,'report');
    if (save_log) save_json(tama_json,'tama');
    if (save_log) save_json(gaze_json,'gaze');
    
    hvcp2_R.disconnect().then(() => {
	  console.log('Disconnected.');
	}).catch((error) => {
	  console.error(error);
	});
    hvcp2_L.disconnect().then(() => {
	  console.log('Disconnected.');
	}).catch((error) => {
	  console.error(error);
	});
    
      
    console.log("Caught SIGINT. Exiting in 2 seconds."); 
    setTimeout(() => {
    console.log("Bye Bye. Tama.");
    process.exit(0);
  }, 3000);
});

function ensureExists(path, mask, cb) {
    if (typeof mask == 'function') { // allow the `mask` parameter to be optional
        cb = mask;
        mask = 484;
    }
    var fs = require('fs');
    fs.mkdir(path, mask, function(err) {
        if (err) {
            if (err.code == 'EEXIST') cb(null); // ignore the error if the folder already exists
            else cb(err); // something else went wrong
        } else cb(null); // successfully created folder
    });
}

function save_json(json_file,file_){
    //console.log(JSON.stringify(json_file, null, '  '));
    let data = JSON.stringify(json_file, null, 2);
    var fs = require('fs');
    fs.writeFile(project_path+'/'+project_path+'_'+file_+'.json', data,(err) => {  
    if (err) throw err;
    console.log('Data written to file');
});
}

function log_data(data,json_object){
            var key = Date.now();
            json_object[key] = []; // empty Array, which you can push() values into
            json_object[key].push(data);
}
function log_config_file(json_object){
            var key = Date.now();
            json_object['start_time'] = []; // empty Array, which you can push() values into
            json_object['start_time'].push(start_time);
    
            json_object['stop_time'] = []; // empty Array, which you can push() values into
            json_object['stop_time'].push(key);
    
            json_object['pictures'] = []; // empty Array, which you can push() values into
            json_object['pictures'].push(pictures);
    
            json_object['gaze'] = []; // empty Array, which you can push() values into
            json_object['gaze'].push(gaze);
    
            json_object['pixel_ring'] = []; // empty Array, which you can push() values into
            json_object['pixel_ring'].push(pixel_ring_ON);
    
            json_object['assistant'] = []; // empty Array, which you can push() values into
            json_object['assistant'].push(googleAssistant);
    
            json_object['head'] = []; // empty Array, which you can push() values into
            json_object['head'].push(HEAD);
    
            json_object['test_mode'] = []; // empty Array, which you can push() values into
            json_object['test_mode'].push(test_mode);
    
            json_object['number_gaze_interactions'] = []; // empty Array, which you can push() values into
            json_object['number_gaze_interactions'].push(number_gaze_interacitons);
    
            json_object['number_requests'] = []; // empty Array, which you can push() values into
            json_object['number_requests'].push(number_requests);
    
            json_object['number_stopped_gaze_interacitons'] = []; // empty Array, which you can push() values into
            json_object['number_stopped_gaze_interacitons'].push(number_stopped_gaze_interacitons);
    
            json_object['GAZE_LIMIT'] = []; // empty Array, which you can push() values into
            json_object['GAZE_LIMIT'].push(GAZE_LIMIT);
    
            json_object['abort_limit'] = []; // empty Array, which you can push() values into
            json_object['abort_limit'].push(abort);
}
