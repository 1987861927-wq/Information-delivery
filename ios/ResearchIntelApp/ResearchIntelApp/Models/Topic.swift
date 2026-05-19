import Foundation

struct Topic: Identifiable, Codable, Hashable {
    var id: String { slug }
    let slug: String
    let name: String
    let description: String
    let keywords: [String]
}
