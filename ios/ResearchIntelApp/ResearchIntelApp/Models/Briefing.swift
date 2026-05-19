import Foundation

struct Briefing: Codable {
    let date: String
    let title: String
    let topics: [String]
    let highlights: [Article]
    let articles: [Article]
}
