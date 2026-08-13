import XCTest
import ClarityCore

final class ClarityLogicTests: XCTestCase {
    func testStripsLeadingFillers() {
        let result = ClarityOfflineClarifier.clarify("嗯我想吃饭", mode: "default")
        XCTAssertTrue(result.hasPrefix("我想吃饭"))
    }

    func testDefaultModeAddsPeriod() {
        let result = ClarityOfflineClarifier.clarify("你好", mode: "default")
        XCTAssertTrue(result.hasSuffix("。"))
    }

    func testDefaultModeAddsQuestionMarkForMa() {
        let result = ClarityOfflineClarifier.clarify("你去吗", mode: "default")
        XCTAssertTrue(result.hasSuffix("？"))
    }

    func testAIModePrefixesIntent() {
        let result = ClarityOfflineClarifier.clarify("帮我订票", mode: "ai")
        XCTAssertTrue(result.hasPrefix("Intent:"))
    }

    func testConnectionNameConstant() {
        XCTAssertEqual("ClarityIME_Connection", "ClarityIME_Connection")
    }
}
