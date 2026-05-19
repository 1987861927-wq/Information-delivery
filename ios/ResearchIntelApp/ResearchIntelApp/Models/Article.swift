import Foundation

struct Article: Identifiable, Codable, Hashable {
    let id: String
    let source: String
    let sourceId: String?
    let title: String
    let chineseTitle: String?
    let abstract: String?
    let summary: String?
    let url: String
    let doi: String?
    let publishedAt: Date?
    let topics: [String]
    let relevanceScore: Double
    let qualityScore: Double
    let isPreprint: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case source
        case sourceId = "source_id"
        case title
        case chineseTitle = "chinese_title"
        case abstract
        case summary
        case url
        case doi
        case publishedAt = "published_at"
        case topics
        case relevanceScore = "relevance_score"
        case qualityScore = "quality_score"
        case isPreprint = "is_preprint"
    }
}
