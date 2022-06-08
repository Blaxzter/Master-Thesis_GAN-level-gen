package ab.server.proxy.message;

import org.json.simple.JSONObject;

import ab.server.ProxyMessage;

public class ProxyLevelSelectMessage implements ProxyMessage<Object> {

	int levelIndex = 0;
	
	public ProxyLevelSelectMessage(int levelIndex) {
		this.levelIndex = levelIndex;
	}
	
	@Override
	public String getMessageName() {
		return "selectlevel";
	}

	@SuppressWarnings("unchecked")
	@Override
	public JSONObject getJSON() {
		JSONObject o = new JSONObject();
		o.put("levelIndex", levelIndex);
		return o;
	}

	@Override
	public Object gotResponse(JSONObject data) {
		
		System.out.println("Level Select");
		return new Object();
	}

}
