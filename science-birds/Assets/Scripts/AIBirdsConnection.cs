// SCIENCE BIRDS: A clone version of the Angry Birds game used for 
// research purposes
// 
// Copyright (C) 2016 - Lucas N. Ferreira - lucasnfe@gmail.com
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>
//

﻿using UnityEngine;
using System.Runtime.InteropServices;
using System.Collections;
using System.Collections.Generic;
using System;
 using System.Globalization;
 using SimpleJSON;
using UnityEngine.SceneManagement;

delegate IEnumerator Handler(JSONNode data, WebSocket serverSocket);

public class Message {

	public string data;
	public string time;
}

public class AIBirdsConnection : ABSingleton<AIBirdsConnection>
{

	public bool _levelLoaded = false;
	Dictionary<String, Handler> handlers;
	WebSocket generatorWebSocket;
	WebSocket aiWebSocket;

	private bool listenToAI = false;
	private HUD _hudInstance = null;

	IEnumerator Click(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		float clickX = data[2]["x"].AsFloat;
		float clickY = Screen.height - data[2]["y"].AsFloat;

		Vector2 clickPos = new Vector2 (clickX, clickY);

		HUDInstance.SimulateInputEvent = 1;
		HUDInstance.SimulateInputPos = clickPos;
		HUDInstance.SimulateInputDelta = clickPos;

		string id = data [0];
		string message = "[" + id + "," + "{}" + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));	
	#else
		serverSocket.Send(message);	
	#endif
	}

	IEnumerator Drag(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		float dragX = data[2]["x"].AsFloat;
		float dragY = data[2]["y"].AsFloat;

		float dragDX = dragX + data[2]["dx"].AsFloat;
		float dragDY = dragY + data[2]["dy"].AsFloat;

		Vector2 dragPos = new Vector2 (dragX, Screen.height - dragY);
		Vector2 deltaPos = new Vector2 (dragDX, Screen.height - dragDY);

		HUDInstance.SimulateInputEvent = 1;
		HUDInstance.SimulateInputPos = dragPos;
		HUDInstance.SimulateInputDelta = deltaPos;

		string id = data [0];
		string message = "[" + id + "," + "{}" + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif

	}

	IEnumerator MouseWheel(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		float delta = data[2]["delta"].AsFloat;

		HUDInstance.CameraZoom (-delta);

		string id = data [0];
		string message = "[" + id + "," + "{}" + "]";


	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif

	}

	IEnumerator Screenshot(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		Texture2D screenshot = new Texture2D (Screen.width, Screen.height, TextureFormat.ARGB32, true);
		screenshot.ReadPixels (new Rect (0, 0, Screen.width, Screen.height), 0, 0, true);
		screenshot.Apply();

		string image = System.Convert.ToBase64String (screenshot.EncodeToPNG ());
	
		string id = data [0];

		Message msg = new Message ();
		msg.data = "data:image/png;base64," + image;
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif

	}

	IEnumerator SelectLevel(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		int levelIndex = data[2]["levelIndex"].AsInt;

		Debug.Log ("Level index:" + levelIndex);

		LevelList.Instance.SetLevel(levelIndex - 1);
		ABSceneManager.Instance.LoadScene ("GameWorld");

		string id = data [0];
		string message = "[" + id + "," + "{}" + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif

	}

	IEnumerator LoadScene(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		string scene = data[2]["scene"];
		ABSceneManager.Instance.LoadScene (scene);

		string id = data [0];
		string message = "[" + id + "," + "{}" + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif

	}
	
	
	IEnumerator Score(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		string id = data [0];

		Message msg = new Message ();
		msg.data = HUDInstance.GetScore ().ToString();
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif
	}	
	
	
	IEnumerator Solve(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		string id = data [0];
		ABGameWorld gameWorld = ABGameWorld.Instance;
		bool result = gameWorld.Solve();

		Message msg = new Message ();
		msg.data = result.ToString();
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif
	}

	IEnumerator GetData(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		while (HUDInstance == null)
		{
			yield return null;
		}
		
		string id = data [0];

		string msgData = 
			"{" +
			"'damage': " + HUDInstance.GetDamage().ToString(CultureInfo.InvariantCulture) +
			"'death': " + HUDInstance.GetDeath().ToString() +
			"'score': " + HUDInstance.GetScore().ToString() +
			"}";
		
		Message msg = new Message ();
		msg.data = msgData;
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif
	}
	
	IEnumerator LevelsLoaded(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		string id = data [0];

		Message msg = new Message ();
		msg.data = _levelLoaded.ToString();
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif
	}

	IEnumerator AiModus(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		string id = data [0];
		string value = data[2];

		bool aiMode = data[2]["mode"].AsBool;
		int startLevel = data[2]["startLevel"].AsInt;
		int endLevel = data[2]["endLevel"].AsInt;

		if (startLevel != -1 && startLevel != LevelList.Instance.CurrentIndex)
		{
			LevelList.Instance.SetLevel(startLevel - 1);
			ABSceneManager.Instance.LoadScene ("GameWorld");
			yield return new WaitForEndOfFrame ();
		}
		else
		{
			startLevel = LevelList.Instance.CurrentIndex;
		}

		if (endLevel != -1 && endLevel < startLevel)
		{
			Debug.LogError("End level lower then start level.");
			LevelList.Instance.RequiredLevel(endLevel - startLevel);
		}
		
		this.listenToAI = aiMode;
		
		LevelList.Instance.ClearLevelsPlayed();
		
		Message msg = new Message ();
		msg.data = this.listenToAI.ToString();
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif
	}
	
	IEnumerator AllLevelsPlayed(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		string id = data [0];

		Message msg = new Message ();
		msg.data = LevelList.Instance.AllLevelPlayed().ToString();
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif
	}

	IEnumerator GameState(JSONNode data, WebSocket serverSocket) {

		yield return new WaitForEndOfFrame ();

		string id = data [0];

		string currentScence = SceneManager.GetActiveScene().name;

		if (currentScence == "GameWorld") {

			if (ABGameWorld.Instance.LevelCleared ()) {

				currentScence = "LevelCleared";
			} 
			else if (ABGameWorld.Instance.LevelFailed ()) {

				currentScence = "LevelFailed";
			}
		}

		Message msg = new Message ();
	
		msg.data = currentScence;
		msg.time = DateTime.Now.ToString ();

		string json = JsonUtility.ToJson (msg);
		string message = "[" + id + "," + json + "]";

	#if UNITY_WEBGL && !UNITY_EDITOR
		serverSocket.Send(System.Text.Encoding.UTF8.GetBytes(message));
	#else
		serverSocket.Send(message);	
	#endif
	}

	public void InitHandlers() {

		handlers = new Dictionary<string, Handler> ();

		handlers ["click"]        = Click;
		handlers ["drag"]         = Drag;
		handlers ["mousewheel"]   = MouseWheel;
		handlers ["screenshot"]   = Screenshot;
		handlers ["gamestate"]    = GameState;
		handlers ["loadscene"]    = LoadScene;
		handlers ["selectlevel"]  = SelectLevel;
		handlers ["score"]        = Score;
		handlers ["getdata"]      = GetData;
		handlers ["levelsloaded"] = LevelsLoaded;
		handlers ["solve"]        = Solve;
		handlers ["aimodus"]      = AiModus;
		handlers ["alllevelsplayed"] = AllLevelsPlayed;
	}

	// Use this for initialization
	IEnumerator Start () {

		DontDestroyOnLoad (this.gameObject);

		InitHandlers ();
		
		generatorWebSocket = new WebSocket(new Uri("ws://localhost:9001/"));
		yield return StartCoroutine(generatorWebSocket.Connect());
		
		while (true) {
			
			string generatorReply = generatorWebSocket.RecvString();

			if (generatorReply != null) {

				JSONNode data = JSON.Parse(generatorReply);

				string type = data [1];

				Debug.Log("Generator message: " + type);

				if (handlers[type] != null) {

					StartCoroutine(handlers [type] (data, generatorWebSocket));
				} 
				else {
					
					Debug.Log("Invalid message: " + type);
				}
			}

			if (generatorWebSocket.error != null) {
				yield return new WaitForSeconds (1);

				generatorWebSocket = new WebSocket(new Uri("ws://localhost:9001/"));
				yield return StartCoroutine(generatorWebSocket.Connect());
			}

			if (listenToAI) {
				if (aiWebSocket == null)
				{
					aiWebSocket = new WebSocket(new Uri("ws://localhost:9000/"));
					yield return StartCoroutine(aiWebSocket.Connect());
				}
				else
				{
					string aiReply = aiWebSocket.RecvString();
					
					if (aiReply != null) {

						JSONNode data = JSON.Parse(aiReply);

						string type = data [1];

						Debug.Log("AI message: " + type);

						if (handlers[type] != null) {

							StartCoroutine(handlers [type] (data, aiWebSocket));
						} 
						else {
						
							Debug.Log("Invalid message: " + type);
						}
					}
					
					if (aiWebSocket.error != null) {

						Debug.Log ("Error: " + aiWebSocket.error);

						yield return new WaitForSeconds (1);

						aiWebSocket = new WebSocket(new Uri("ws://localhost:9000/"));
						yield return StartCoroutine(aiWebSocket.Connect());
					}
				}
			}

			yield return 0;
		}

//		socket.Close();
	}

	public HUD HUDInstance
	{
		get { return _hudInstance; }
		set { _hudInstance = value; }
	}

	public bool LevelLoaded
	{
		get { return _levelLoaded; }
		set { _levelLoaded = value; }
	}
}
