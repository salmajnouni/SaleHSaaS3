using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace IntegraAI.RevitPlugin
{
    public class IntegraAIConnector
    {
        private readonly HttpClient _httpClient;

        public IntegraAIConnector(string baseUrl = "http://localhost:8000")
        {
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(baseUrl)
            };
        }

        public async Task<string> SendCompliancePayloadAsync(string jsonPayload)
        {
            var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");
            var response = await _httpClient.PostAsync("/api/v1/validation/check-compliance", content);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsStringAsync();
        }

        public async Task<string> FindRouteAsync(string jsonPayload)
        {
            var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");
            var response = await _httpClient.PostAsync("/api/v1/routing/find-path", content);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadAsStringAsync();
        }
    }
}
