import Foundation

final class APIClient: ObservableObject {
    static let shared = APIClient()

    private let baseURL = URL(string: "http://127.0.0.1:8000/api/v1")!
    private let decoder: JSONDecoder

    private init() {
        decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
    }

    func fetchTopics() async throws -> [Topic] {
        let url = baseURL.appending(path: "topics")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try decoder.decode([Topic].self, from: data)
    }

    func fetchTodayBriefing(topic: String? = nil) async throws -> Briefing {
        var url = baseURL.appending(path: "briefings/today")
        if let topic {
            url.append(queryItems: [URLQueryItem(name: "topic", value: topic)])
        }
        let (data, _) = try await URLSession.shared.data(from: url)
        return try decoder.decode(Briefing.self, from: data)
    }
}
