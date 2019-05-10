/* ========================================================================
 * Copyright (C) 2019 The MITRE Corporation.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ======================================================================== */

using System;
using System.Net;
using System.Text;
using System.Threading.Tasks;

namespace RigettiUpdateProxy
{
    /// <summary>
    /// This program is used to fix the bug reported in https://github.com/rigetti/qvm/issues/86.
    /// 
    /// Basically, Forest's compiler and simulator (Quilc and QVM) check Rigetti's
    /// server for version updates upon startup. If this check fails (say, for example,
    /// if you're behind a proxy or if their servers are down), both programs will crash.
    /// 
    /// We worked around this by redirecting traffic aimed at downloads.rigetti.com to
    /// our local machine by putting this line in our HOSTS file:
    /// 
    /// 	127.0.0.1	downloads.rigetti.com
    /// 
    /// This server just pretends to be the Rigetti download server, and returns the response
    /// that server returns (at the time of our testing). It's just a JSON string with
    /// some version number attached.
    /// </summary>
    /// <remarks>
    /// Note that you're going to need to run this as administrator, because it uses port 80.
    /// If you're running it from Visual Studio's debugger, just run VS itself as admin.
    /// If you're invoking it through the console directly via dotnet, run the console as admin.
    /// </remarks>
    class Program
    {
        /// <summary>
        /// The HTTP server
        /// </summary>
        private static HttpListener Server;

        /// <summary>
        /// A separate thread the server will run in
        /// </summary>
        private static Task ServerTask;

        /// <summary>
        /// Entry point
        /// </summary>
        /// <param name="Args">Not used</param>
        static void Main(string[] Args)
        {
            // Launch the server, set it up to listen for requests to the version-check URL
            Server = new HttpListener();
            Server.Prefixes.Add($"http://127.0.0.1:80/qcs-sdk/version/");
            Server.Start();
            ServerTask = Task.Run(RunServer);
            Console.WriteLine("Server's up, press enter to exit.");

            // Shut down and clean up on close
            Console.ReadLine();
            Server.Stop();
            Server.Close();
            ServerTask = null;
        }

        /// <summary>
        /// This is the HTTP server's execution loop.
        /// </summary>
        static void RunServer()
        {
            while (Server.IsListening)
            {
                HttpListenerContext context;
                try
                {
                    // Get a new request from the listener
                    context = Server.GetContext();
                }
                catch (HttpListenerException)
                {
                    // If the context breaks unexpectedly, just ignore it and start over
                    continue;
                }

                // Respond with the JSON string no matter what, since that's all we really care about
                using (HttpListenerResponse response = context.Response)
                {
                    // This is the version JSON string that QVM and Quilc expect
                    string versionString = "{\"sdk\":\"2.7.0\", \"quilc\":\"1.7.2\", \"qvm\":\"1.7.2\"}";

                    // Encode it and send it, both programs seem happy enough with this response
                    byte[] buffer = Encoding.UTF8.GetBytes(versionString);
                    response.ContentLength64 = buffer.Length;
                    response.OutputStream.Write(buffer, 0, buffer.Length);
                }
            }
        }

    }
}
