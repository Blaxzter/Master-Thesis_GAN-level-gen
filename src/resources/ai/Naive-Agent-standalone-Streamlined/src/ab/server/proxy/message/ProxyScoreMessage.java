package ab.server.proxy.message;

import org.json.simple.JSONObject;

import ab.server.ProxyMessage;

public class ProxyScoreMessage implements ProxyMessage<Integer> {

	@Override
	public String getMessageName() {
		
		return "score";
	}

	@Override
	public JSONObject getJSON() {
		
		return new JSONObject();
	}

	@Override
	public Integer gotResponse(JSONObject data) {
		String score = (String) data.get("data");
		
		Integer intScore = Integer.decode(score);
	        
	     System.out.println("score: " + score);
	     return intScore;
	}
}
