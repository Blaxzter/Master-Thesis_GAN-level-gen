package ab.server.proxy.message;

import org.json.simple.JSONObject;

import ab.server.ProxyMessage;

public class ProxyLoadSceneMessage implements ProxyMessage<Object> {

	String scene;

	public ProxyLoadSceneMessage(String scene) {
		this.scene = scene;
	}

	@Override
	public String getMessageName() {
		return "loadscene";
	}

	@SuppressWarnings("unchecked")
	@Override
	public JSONObject getJSON() {
		JSONObject o = new JSONObject();
		o.put("scene", scene);
		return o;
	}

	@Override
	public Object gotResponse(JSONObject data) {

		System.out.println("Load Scene");

		return new Object();
	}

}
